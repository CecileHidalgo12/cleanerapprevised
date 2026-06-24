import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(page_title="PDF Cleaner", page_icon="⚖️")
st.title(" Watermark Remover")

uploaded_file = st.file_uploader("Upload your PDF", type="pdf")

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    st.subheader("1. Identify Your Watermark")
    st.write("Scan the images found on Page 1. Find the ID of the diagonal watermark.")

    # Get images from the first page
    images = doc[0].get_images(full=True)
    
    if images:
        # Create a grid to show images
        cols = st.columns(3)
        for i, img in enumerate(images):
            xref = img[0]
            try:
                # Extract the image as a PNG
                pix = fitz.Pixmap(doc, xref)
                
                # If image is CMYK, convert to RGB for web display
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                img_data = pix.tobytes("png")
                
                # Show in the grid
                with cols[i % 3]:
                    st.image(img_data, caption=f"ID: {xref}", use_container_width=True)
                    st.write(f"**XRef ID: {xref}**")
            except Exception as e:
                continue

    st.divider()

    # Step 2: User enters the IDs they want to kill
    st.subheader("2. Remove and Download")
    ids_to_remove = st.text_input("Enter the IDs you want to remove (comma separated, e.g., 3847, 3848)")

    if st.button("Clean and Download PDF") and ids_to_remove:
        # Convert input string to a list of integers
        target_ids = [int(x.strip()) for x in ids_to_remove.split(",")]
        
        # Process every page
        for page in doc:
            for tid in target_ids:
                page.delete_image(tid)
        
        # Save output
        output_bytes = doc.write()
        st.success("PDF cleaned successfully!")
        st.download_button(
            label="Download Cleaned PDF",
            data=output_bytes,
            file_name=f"cleaned_{uploaded_file.name}",
            mime="application/pdf"
        )
