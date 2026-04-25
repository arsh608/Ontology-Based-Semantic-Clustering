def split_into_sentences(text):
    sentences = [line.strip() for line in text.split('\n') if line.strip()]
    return sentences

from docx import Document
def get_sentences_from_files(files):
    sentences = []
    for file in files:
        name = file.filename.lower()
        if name.endswith('.txt'):
            text = file.read().decode('utf-8')
            file_sentences = [line.strip() for line in text.split('\n') if line.strip()]
            sentences.extend(file_sentences)

        elif name.endswith('.docx'):
            doc = Document(file)
            file_sentences = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
            sentences.extend(file_sentences)

        else:
            raise ValueError("There are no sentences in the file or unsupported file format.")
        
        file.seek(0)
    return sentences
