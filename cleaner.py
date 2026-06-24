import streamlit as st
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="PDF Cleaner", page_icon="⚖️")
st.title("Watermark Remover (True Batch)")

uploaded_files = st.file_uploader("Upload your PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    # ----------------------------------------------------
    # Step 1: Extract all unique images from the first file to find the "Fingerprint"
    # ----------------------------------------------------
    st.subheader("1. Select the Watermark to Remove")
    st.write("We will extract unique images from your first file. Select the one you want wiped from ALL files.")

    first_file = uploaded_files[0]
    first_file_bytes = first_file.read()
    doc_preview = fitz.open(stream=first_file_bytes, filetype="pdf")
    
    # We will map image bytes to their sample XRef to show them uniquely
    unique_images = {}
    
    for page in doc_preview:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc_preview.extract_image(xref)
            if base_image:
                img_bytes = base_image["image"]
                # Use the image bytes as a unique key so we don't show duplicates
                if img_bytes not in unique_images:
                    unique_images[img_bytes] = xref

    if unique_images:
        cols = st.columns(3)
        selected_watermark_bytes = None
        
        # Display images with a radio button choice or selection
        image_list = list(unique_images.items())
        
        # Let user choose via a selectbox or radio based on index
        options = [f"Image Option {idx+1} (XRef {xref})" for idx, (bytes_data, xref) in enumerate(image_list)]
        selected_option = st.radio("Choose which image is the watermark:", options)
        selected_index = options.index(selected_option)
        
        # Store the raw bytes of the chosen watermark
        target_watermark_bytes = image_list[selected_index][0]

        # Preview what they are currently selecting in a grid layout
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
    # Step 2: Batch Process Entire List
    # ----------------------------------------------------
    st.subheader("2. Run Batch Purge")
    
    if target_watermark_bytes and st.button("Delete Watermark From All Files"):
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
                
                # Dynamic Scan: Find IDs in THIS specific file that match our target watermark's data
                for page in doc:
                    for img in page.get_images(full=True):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        if base_image and base_image["image"] == target_watermark_bytes:
                            bad_xrefs.add(xref)
                
                # Delete those matching IDs from every page
                if bad_xrefs:
                    for page in doc:
                        for xref in bad_xrefs:
                            try:
                                page.delete_image(xref)
                            except Exception:
                                pass
                    
                    # Re-optimize/compact PDF structure to completely wipe deleted object layers
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
                    st.info(f"ℹ️ Skipped {uploaded_file.name}: Watermark image data not found inside.")
                    
                st.markdown("---")
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {e}")
