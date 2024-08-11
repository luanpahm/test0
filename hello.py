import fitz  # PyMuPDF


class PDFTextExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.page = self.doc.load_page(0)  # Load the first page
        self.result = {
            'spans': [],
            'lines': [],
            'annots': []
        }

    def extract_text_with_coordinates(self):
        text_instances = self.page.get_text("dict")["blocks"]
        lines = []  # Store lines of text along with their coordinates

        for block in text_instances:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    line_coords = None
                    for span in line["spans"]:
                        if line_text:
                            line_text += ""
                        line_text += span["text"]
                        if not line_coords:
                            line_coords = span["bbox"]
                        else:
                            # Merge the bounding boxes
                            line_coords = [
                                min(line_coords[0], span["bbox"][0]),  # x0
                                min(line_coords[1], span["bbox"][1]),  # y0
                                max(line_coords[2], span["bbox"][2]),  # x1
                                max(line_coords[3], span["bbox"][3])  # y1
                            ]
                    lines.append((line_text, line_coords))
        return lines

    def highlight_text(self, output_path):
        lines = self.extract_text_with_coordinates()

        # Highlight the text by drawing rectangles around the bounding boxes
        for text, bbox in lines:
            print(text)
            rect = fitz.Rect(bbox)
            self.page.draw_rect(rect, color=(1, 0, 0), width=0.5)  # Red rectangle with 0.5 width

        # Save the modified PDF
        self.doc.save(output_path)
        print(f"Highlighted PDF saved to {output_path}")

    def close(self):
        self.doc.close()
class PartsExtractor:
    def __init__(self, extracted_data):
        self.extracted_data = extracted_data

if __name__ == "__main__":
    pdf_path = "2.pdf"
    output_path = "1_highlighted.pdf"

    extractor = PDFTextExtractor(pdf_path)
    result = extractor.extract_text_with_coordinates()
    extractor.close()
    print(result)
