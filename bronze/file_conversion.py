from docx import Document
import json
import csv
import pandas as pd

def docx_jsonarray_to_csv(input_docx, output_csv):
    doc = Document(input_docx)
    full_text = "\n".join(p.text for p in doc.paragraphs)

    start = full_text.find("[")
    end = full_text.rfind("]") + 1

    if start == -1 or end == -1:
        print(f"No JSON array found in {input_docx}")
        return

    data = json.loads(full_text[start:end])
    headers = data[0].keys()

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    print(f" Created {output_csv}")


def excel_to_csv(input_xlsx, output_csv):
    df = pd.read_excel(input_xlsx)
    df.to_csv(output_csv, index=False)
    print(f" Created {output_csv}")


if __name__ == "__main__":
    docx_jsonarray_to_csv("vitals.docx", "vitals.csv")
    docx_jsonarray_to_csv("labs- Ajay kumar.docx", "labs.csv")
    excel_to_csv("ehr.xlsx", "ehr.csv")

    print("\n All files converted successfully!")