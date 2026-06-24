import streamlit as st
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="PDF Cleaner", page_icon="⚖️")
st.title("Watermark Remover (Multi-Select Batch)")

uploaded_files = st.file_uploader("Upload your PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    # ----------------------------------------------------
    # Step 1: Extract and display all unique images from the first file
    # ----------------------------------------------------
    st.subheader("1. Select All Watermarks to Remove")
    st.write("Check the box for **every** image you want completely wiped from ALL files.")

    first_file = uploaded_files[0]
    first_file_bytes = first_file.read()
    doc_preview = fitz.open(stream=first_file_bytes, filetype="pdf")
    
    # Map raw image bytes to their sample XRef ID to prevent duplicate previews
    unique_images = {}
    for page in doc_preview:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc_preview.extract_image(xref)
            if base_image:
                img_bytes = base_image["image"]
                if img_bytes not in unique_images:
                    unique_images[img_bytes] = xref

    # Track which images the user selects
    selected_watermarks = []

    if unique_images:
        cols = st.columns(3)
        
        # Display each unique image in a grid with an independent checkbox
        for idx, (img_bytes, xref) in enumerate(unique_images.items()):
            with cols[idx % 3]:
                try:
                    st.image(img_bytes, caption=f"Image ID: {xref}", use_container_width=True)
                    # If checked, add this image's raw bytes to our target list
                    if st.checkbox(f"Remove this", key=f"chk_{xref}"):
                        selected_watermarks.append(img_bytes)
                except Exception:
                    continue
    else:
        st.warning("No images found in the first PDF.")

    st.divider()

    # ----------------------------------------------------
    # Step 2: Batch Process Entire List using all selected "fingerprints"
    # ----------------------------------------------------
    st.subheader("2. Run Batch Purge")
    
    if st.button("Delete Selected Watermarks From All Files"):
        if not selected_watermarks:
            st.error("Please check at least one image box above before running the purge.")
        else:
            st.write("### Processing Status")
            
            for uploaded_file in uploaded_files:
                try:
                    # Reset stream pointer and load file
                    if uploaded_file == first_file:
                        file_bytes = first_file_bytes
                    else:
                        file_bytes = uploaded_file.read()
                        
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    bad_xrefs = set()
                    
                    # Scan every image in this document
                    for page in doc:
                        for img in page.get_images(full=True):
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            
                            # Check if this image matches ANY of our selected targets
                            if base_image and base_image["image"] in selected_watermarks:
                                bad_xrefs.add(xref)
                    
                    # Purge all identified bad XRefs from every page
                    if bad_xrefs:
                        for page in doc:
                            for xref in bad_xrefs:
                                try:
                                    page.delete_image(xref)
                                except Exception:
                                    pass
                        
                        # Pack and clean the PDF structure
                        output_bytes = doc.write(garbage=3, deflate=True)
                        
                        st.success(f"✅ Cleaned: {uploaded_file.name}")
                        st.download_button(
                            label=f"Download cleaned_{uploaded_file.name}",
                            data=output_bytes,
                            file_name=f"cleaned_{uploaded_file.name}",
                            mime="application/pdf",
                            key=f"dl_{uploaded_file.name}"
                        )
                    else:
                        st.info(f"ℹ️ Skipped {uploaded_file.name}: None of the selected watermarks found.")
                        
                    st.markdown("---")
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {e}")
