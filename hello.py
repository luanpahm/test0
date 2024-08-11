import fitz  # PyMuPDF


class PDFTextExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.page = self.doc.load_page(0)  # Load the first page
        self.result = {
            'spans': [],
            'lines': [],
            'annots': [],
            'total_spans': []
        }

    def extract_text_with_coordinates(self):
        text_instances = self.page.get_text("dict")["blocks"]
        lines = []  # Store lines of text along with their coordinates
        total_spans = []
        for block in text_instances:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    line_coords = None
                    details = []
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
                        details.append(span)
                        total_spans.append(span)

                    payload = {
                        'text_line': line_text.strip(),
                        'bboxes': list(line_coords),
                        'details': details
                    }
                    lines.append(payload)
        self.result['spans'] = lines
        self.result['total_spans'] = total_spans
        return self.result

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
        self.information = extracted_data
        self.spans = self.information["spans"]
        self.annots = self.information["annots"]
        self.total_spans = self.information["total_spans"]
        self.first_page = 0

    def get_doc_symbol(self):
        doc_symbol = None
        for span in self.spans:
            check_str = span['text_line'].replace(' ', '').lower()
            if check_str.startswith('số'):
                if ':' in check_str and '/' in check_str and '-' in check_str:
                    doc_symbol = span
                    break
        return doc_symbol

    def get_unit_name(self, doc_symbol, national_crest):
        unit_spans = None
        first_unit = None
        sub_unit = []
        payload = {
            'main_unit': None,
            'sub_unit': None
        }
        for span in self.spans:
            check_str = span['text_line'].replace(' ', '').upper()
            if check_str.startswith('TẬPĐ') and \
                    (check_str.endswith('VIETTEL') or
                     check_str.endswith('QUÂNĐỘI') or
                     check_str.endswith('QUÂNĐÔỊ')):
                first_unit = span
                break
        if first_unit is not None:
            # if found first unit, find subunit
            last_first_unit_span = first_unit['details'][0]['bbox']
            national_name_span = national_crest['national_name']['details'][0]
            doc_symbol_span = doc_symbol['details'][0]
            y_min = last_first_unit_span[-1]
            x_max = national_name_span['bbox'][0]
            y_max = doc_symbol_span['bbox'][1]
            if len(self.total_spans) != 0:
                for span in self.total_spans:
                    x0_span = span['bbox'][0]
                    y0_span = span['bbox'][1]
                    if x0_span < x_max and y_min < y0_span < y_max:
                        if span['text'].strip() != '':
                            sub_unit.append(span)
        if len(sub_unit) != 0:
            payload.update({'sub_unit': sub_unit})
        payload.update({'main_unit': first_unit})
        return payload

    def get_national_name(self,doc_symbol):
        national_name = None
        crest = None
        y_max = doc_symbol['details'][0]['bbox'][1]

        for span in self.spans:
            check_str = span['text_line'].replace(' ', '')
            if check_str.startswith('CỘNGH') and \
                    check_str.endswith('TNAM'):
                national_name = span
                break
        if national_name is not None:
            crest = []
            delta_x = 5
            x_min = national_name['details'][0]['bbox'][0]-delta_x
            y_min = national_name['details'][0]['bbox'][1]
            for spx in self.total_spans:
                spx_x0 = spx['bbox'][0]
                spx_y0 = spx['bbox'][1]
                if spx_x0 > x_min and y_min < spx_y0 < y_max:
                    if spx['text'].strip() != '':
                        crest.append(spx)
            if len(crest) == 0:
                crest = None
        payload = {
            'national_name': national_name,
            'crest': crest
        }
        return payload

    def get_document_location_n_date(self, national_crest):
        location_n_time = None
        crest = national_crest['crest']
        x_min = crest[0]['bbox'][0]
        y_min = crest[0]['bbox'][1]
        # y_max = national_name['details'][0]['bbox'][1]
        for span in self.spans:
            x0_span = span['bboxes'][0]
            y0_span = span['bboxes'][1]
            if x0_span >= x_min and y0_span > y_min:
                check_str = span['text_line'].strip().lower()
                if 'ngày' in check_str and 'tháng' and check_str or 'năm' and check_str:
                    location_n_time = span
                    break
        return location_n_time

            # print(span)


    def get_document_type_n_subject(self):
        pass

    def get_recipient(self):
        pass

    def get_signer_title(self):
        pass

    def get_page_number(self):
        pass


if __name__ == "__main__":
    pdf_path = "3.pdf"
    output_path = "1_highlighted.pdf"

    extractor = PDFTextExtractor(pdf_path)
    extracted_info = extractor.extract_text_with_coordinates()
    extractor.close()

    instance = PartsExtractor(extracted_info)
    doc_symbol = instance.get_doc_symbol()
    national_name = instance.get_national_name(doc_symbol)

    unit_name = instance.get_unit_name(doc_symbol, national_name)
    location_n_time = instance.get_document_location_n_date(national_name)
    print(doc_symbol)
    print(national_name)
    print(unit_name)
    print(location_n_time)

