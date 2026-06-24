import streamlit as st
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="PDF Cleaner", page_icon="⚖️")
st.title("Watermark Remover (Multi-File)")

# Enable multiple file uploads
uploaded_files = st.file_uploader("Upload your PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    # ----------------------------------------------------
    # Step 1: Preview images from the FIRST file to find the ID
    # ----------------------------------------------------
    st.subheader("1. Identify Your Watermark")
    st.write("Scanning the first uploaded file to identify the watermark image ID. Find the ID of the diagonal watermark below:")

    first_file = uploaded_files[0]
    # Read into bytes so we don't exhaust the stream if we need it later
    first_file_bytes = first_file.read()
    doc_preview = fitz.open(stream=first_file_bytes, filetype="pdf")
    
    images = doc_preview[0].get_images(full=True)
    
    if images:
        cols = st.columns(3)
        for i, img in enumerate(images):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc_preview, xref)
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                img_data = pix.tobytes("png")
                
                with cols[i % 3]:
                    st.image(img_data, caption=f"ID: {xref}", use_container_width=True)
                    st.write(f"**XRef ID: {xref}**")
            except Exception as e:
                continue
    else:
        st.warning("No images found on Page 1 of the first PDF to preview.")

    st.divider()

    # ----------------------------------------------------
    # Step 2: Remove and Download
    # ----------------------------------------------------
    st.subheader("2. Remove and Download")
    ids_to_remove = st.text_input("Enter the IDs you want to remove (comma separated, e.g., 3847, 3848)")

    if ids_to_remove:
        try:
            target_ids = [int(x.strip()) for x in ids_to_remove.split(",") if x.strip()]
        except ValueError:
            st.error("Please enter valid numeric IDs separated by commas.")
            target_ids = []

        if target_ids and st.button("Clean All PDFs"):
            st.write("### Processed Files")
            
            # Loop through all uploaded files
            for uploaded_file in uploaded_files:
                try:
                    # Reset stream pointer if it was the first file, or just read the bytes
                    if uploaded_file == first_file:
                        file_bytes = first_file_bytes
                    else:
                        file_bytes = uploaded_file.read()
                        
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    
                    # Process every page in the current document
                    for page in doc:
                        for tid in target_ids:
                            try:
                                page.delete_image(tid)
                            except Exception:
                                # In case a specific ID doesn't exist on this page/file
                                pass
                    
                    # Save output
                    output_bytes = doc.write()
                    
                    # Display success message and a dedicated download button for each file
                    st.success(f"Cleaned: {uploaded_file.name}")
                    st.download_button(
                        label=f"Download cleaned_{uploaded_file.name}",
                        data=output_bytes,
                        file_name=f"cleaned_{uploaded_file.name}",
                        mime="application/pdf",
                        key=f"dl_{uploaded_file.name}" # Unique key for Streamlit widgets
                    )
                    st.markdown("---")
                except Exception as e:
                    st.error(f"Could not process {uploaded_file.name}: {e}")
