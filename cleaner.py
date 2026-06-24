import streamlit as st
import fitz  # PyMuPDF
import io
import zipfile  # Built-in module to create ZIP archives

st.set_page_config(page_title="PDF Cleaner", page_icon="⚖️")
st.title("Watermark Remover (Batch ZIP Download)")

uploaded_files = st.file_uploader("Upload your PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    # ----------------------------------------------------
    # Step 1: Extract all unique images from the first file
    # ----------------------------------------------------
    st.subheader("1. Select the Watermark to Remove")
    st.write("We will extract unique images from your first file. Select the one you want wiped from ALL files.")

    first_file = uploaded_files[0]
    first_file_bytes = first_file.read()
    doc_preview = fitz.open(stream=first_file_bytes, filetype="pdf")
    
    unique_images = {}
    
    for page in doc_preview:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc_preview.extract_image(xref)
            if base_image:
                img_bytes = base_image["image"]
                if img_bytes not in unique_images:
                    unique_images[img_bytes] = xref

    if unique_images:
        cols = st.columns(3)
        image_list = list(unique_images.items())
        
        options = [f"Image Option {idx+1} (XRef {xref})" for idx, (bytes_data, xref) in enumerate(image_list)]
        selected_option = st.radio("Choose which image is the watermark:", options)
        selected_index = options.index(selected_option)
        
        target_watermark_bytes = image_list[selected_index][0]

        for idx, (img_bytes, xref) in enumerate(image_list):
            try:
                with cols[idx % 3]:
                    st.image(img_bytes, caption=f"Option {idx+1}", use_container_width=True)
            except Exception:
                continue
    else:
        st.warning("No images found in the first PDF.")
        target_watermark_bytes = None

    st.divider()

    # ----------------------------------------------------
    # Step 2: Batch Process and Create ZIP
    # ----------------------------------------------------
    st.subheader("2. Run Batch Purge & Download")
    
    if target_watermark_bytes and st.button("Process All Files"):
        st.write("### Processing Status")
        
        # Create an in-memory buffer to hold the ZIP archive file content
        zip_buffer = io.BytesIO()
        cleaned_count = 0
        
        # Open a ZipFile stream writing to our bytes buffer
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for uploaded_file in uploaded_files:
                try:
                    if uploaded_file == first_file:
                        file_bytes = first_file_bytes
                    else:
                        file_bytes = uploaded_file.read()
                        
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    bad_xrefs = set()
                    
                    for page in doc:
                        for img in page.get_images(full=True):
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            if base_image and base_image["image"] == target_watermark_bytes:
                                bad_xrefs.add(xref)
                    
                    if bad_xrefs:
                        for page in doc:
                            for xref in bad_xrefs:
                                try:
                                    page.delete_image(xref)
                                except Exception:
                                    pass
                        
                        output_bytes = doc.write(garbage=3, deflate=True)
                        
                        # Add the processed PDF file content straight into the ZIP container
                        zip_file.writestr(f"cleaned_{uploaded_file.name}", output_bytes)
                        st.success(f"✅ Cleaned: {uploaded_file.name}")
                        cleaned_count += 1
                    else:
                        st.info(f"ℹ️ Skipped {uploaded_file.name}: Watermark image data not found inside.")
                        
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {e}")
        
        st.divider()
        
        # Offer the unified ZIP download to the user if any files were successfully targeted
        if cleaned_count > 0:
            # Rewind buffer pointer so Streamlit can read from the beginning
            zip_buffer.seek(0)
            
            st.subheader("3. Download Consolidated ZIP Package")
            st.download_button(
                label="📥 Download All Cleaned PDFs (.zip)",
                data=zip_buffer,
                file_name="cleaned_pdfs.zip",
                mime="application/zip"
            )
        else:
            st.warning("No files were successfully processed/modified to pack into a ZIP archive.")
