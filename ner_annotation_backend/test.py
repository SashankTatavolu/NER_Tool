# import xml.etree.ElementTree as ET
# import html
# import re

# def extract_sentences(file_path, output_file):
#     try:
#         # Parse the XML file
#         tree = ET.parse(file_path)
#         root = tree.getroot()

#         # Open the output file to write the sentences
#         with open(output_file, 'w', encoding='utf-8') as f:
#             # Iterate over all the sentence elements
#             for sentence_elem in root.findall(".//sentence"):
#                 # Extract the text attribute (which has the raw sentence text)
#                 raw_text = sentence_elem.get("text")
                
#                 if raw_text:
#                     # Decode HTML/XML entities (like &quot; to ")
#                     decoded_text = html.unescape(raw_text)

#                     # Remove embedded XML tags like <ENAMEX>, <NUMEX>, etc.
#                     clean_text = re.sub(r'<.*?>', '', decoded_text)  # Remove any XML tags

#                     # Write the clean sentence to the file
#                     f.write(clean_text + '\n')

#         print(f"Sentences extracted and saved to {output_file}")
#     except ET.ParseError:
#         print("Invalid XML format")
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")

# # Example usage
# extract_sentences('/home/sashank/Downloads/MWEAnnotationBackend-main/test1.xml', 'extracted_sentences.txt')


import bcrypt

# Password to hash
password = "user@123"

# Hash the password
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

print(hashed_password)
