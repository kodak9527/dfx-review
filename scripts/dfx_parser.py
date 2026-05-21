import os
import re
import json
import sys
import argparse
from datetime import datetime

class DfxParser:
    def __init__(self, template_path, domains_path):
        self.template_path = template_path
        self.domains_path = domains_path
        self.results = {
            "scanTimestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scanDuration": "N/A",
            "totalServices": 0,
            "services": [],
            "crossService": {
                "ranking": [],
                "comparisonMatrix": {},
                "commonGaps": []
            }
        }

    def parse_markdown(self, file_path):
        """解析 LLM 生成的思维链 Markdown 文件"""
        service_name = os.path.basename(file_path).replace("dfx_raw_", "").replace(".md", "")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        service_data = {
            "name": service_name,
            "totalJavaFiles": 0,  # 理想情况下由 collector 提供，此处可预留
            "springBootVersion": "Unknown",
            "buildSystem": "Unknown",
            "businessDomains": [],
            "genericDFX": [],
            "businessDFX": [],
            "scores": {"overall": 0, "genericDFX": 0, "businessDFX": 0, "confidence": "high"},
            "remediation": []
        }

        # 匹配维度和状态判定
        # 格式: - **状态判定**：[Present/Partial/Missing] (允许前后有一定杂乱字符)
        pattern = r"- \*\*维度\*\*：\s*([\d\.]+) (.*?)\n.*?- \*\*意图匹配\*\*：(.*?)\n.*?- \*\*证据提取\*\*：(.*?)\n.*?- \*\*状态判定\*\*：.*?(Present|Partial|Missing)"
        matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)

        generic_scores = []
        business_scores = []

        for match in matches:
            dim_id = match.group(1).strip()
            dim_name = match.group(2).strip()
            intent = match.group(3).strip()
            evidence = match.group(4).strip()
            status = match.group(5).strip().capitalize()

            score_map = {"Present": 1.0, "Partial": 0.5, "Missing": 0.0}
            score = score_map.get(status, 0.0)

            item = {
                "id": dim_id,
                "name": dim_name,
                "status": status.lower(),
                "score": score,
                "summary": intent,
                "evidence": [evidence],
                "recommendations": []
            }

            if dim_id.startswith("2."):
                service_data["genericDFX"].append(item)
                generic_scores.append(score)
            elif dim_id.startswith("3."):
                service_data["businessDFX"].append(item)
                business_scores.append(score)

        # 计算得分
        if generic_scores:
            service_data["scores"]["genericDFX"] = round(sum(generic_scores) / 13, 2) # 固定维度总数
        if business_scores:
            service_data["scores"]["businessDFX"] = round(sum(business_scores) / 11, 2)
        
        service_data["scores"]["overall"] = round(
            service_data["scores"]["genericDFX"] * 0.5 + service_data["scores"]["businessDFX"] * 0.5, 2
        )

        return service_data

    def assemble(self, analyses_dir, output_path):
        """聚合所有分析并生成 HTML"""
        for filename in os.listdir(analyses_dir):
            if filename.startswith("dfx_raw_") and filename.endswith(".md"):
                service_info = self.parse_markdown(os.path.join(analyses_dir, filename))
                self.results["services"].append(service_info)

        self.results["totalServices"] = len(self.results["services"])
        
        # 简单的排序
        self.results["services"].sort(key=lambda x: x["scores"]["overall"], reverse=True)
        self.results["crossService"]["ranking"] = [s["name"] for s in self.results["services"]]

        # 读取模板并注入
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        json_data = json.dumps(self.results, ensure_ascii=False)
        final_html = template.replace("__REPORT_DATA__", json_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        print(f"✅ Dashboard generated: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DFX Analysis Result Parser")
    parser.add_argument("--dir", required=True, help="Directory containing raw markdown analyses")
    parser.add_argument("--template", required=True, help="Path to dashboard-template.html")
    parser.add_argument("--output", default="dfx-report.html", help="Output HTML path")
    
    args = parser.parse_args()
    
    # 简单的运行逻辑
    # 假设 domains.json 在 references 下
    domains_path = os.path.join(os.path.dirname(args.template), "domains.json")
    
    p = DfxParser(args.template, domains_path)
    p.assemble(args.dir, args.output)
