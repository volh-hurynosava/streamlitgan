import subprocess
import os
import sys
import streamlit as st
from PIL import Image
import io
from translation_manager import get_translator
from utils import save_and_prepare_image, scale_back_to_original, cleanup_results

trans = get_translator()
if 'DOCKER' in os.environ:
    parent_dir = '/app'
else:
    parent_dir = os.getcwd()

cyclegan_dir = os.path.join(parent_dir, 'Cyclegan')
script_path = os.path.join(cyclegan_dir, 'test.py')
dataroot = os.path.join(parent_dir, 'datasets', 'test', 'testA')
results_dir = os.path.join(parent_dir, 'results')
checkpoints_dir = os.path.join(parent_dir, 'checkpoints')

sys.path.insert(0, parent_dir)
sys.path.insert(0, cyclegan_dir)

if 'language' not in st.session_state:
    st.session_state.language = "en"
if 'original_image' not in st.session_state:
    st.session_state.original_image = None
if 'styled_image' not in st.session_state:
    st.session_state.styled_image = None
if 'base_name' not in st.session_state:
    st.session_state.base_name = ""
if 'option' not in st.session_state:
    st.session_state.option = "Monet"
if 'scale_info' not in st.session_state:
    st.session_state.scale_info = None
if 'original_size' not in st.session_state:
    st.session_state.original_size = None
if 'file_ready' not in st.session_state:
    st.session_state.file_ready = False
if 'last_uploaded' not in st.session_state:
    st.session_state.last_uploaded = None
if 'current_filename' not in st.session_state:
    st.session_state.current_filename = None
if 'process_requested' not in st.session_state:
    st.session_state.process_requested = False


if not os.path.exists(script_path):
    st.error(trans.get(st.session_state.language, "errors.test_not_found"))
    st.stop()

os.makedirs(dataroot, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

# ===== Page configurations =====
st.set_page_config(
    layout="wide",
    page_title=trans.get(st.session_state.language, "app.title"),
    page_icon="🎨"
)

# ===== Util functions =====
def get_localized_style_names(lang: str) -> list:
    style_keys = ["Monet", "Ukiyoe", "Cezanne", "Vangogh"]
    return [trans.get_style_name(lang, key) for key in style_keys]

def get_english_style_from_localized(localized_name: str, lang: str) -> str:
    style_keys = ["Monet", "Ukiyoe", "Cezanne", "Vangogh"]
    for key in style_keys:
        if trans.get_style_name(lang, key) == localized_name:
            return key
    return "Monet"

def get_painter_text(painter_name: str, language: str) -> str:
    painters_dir = os.path.join(parent_dir, "painters")
    filename = f"{painter_name}_{language}.txt"
    filepath = os.path.join(painters_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return trans.get(st.session_state.language, "errors.painter_text_error")

def display_images_and_downloads(original_img, styled_img, base_name, style_option, lang):
    display_comparison(original_img, styled_img)
    
    st.markdown("---")
    col_dl1, col_dl2= st.columns(2)
    
    with col_dl1:
        buf_png = io.BytesIO()
        styled_img.save(buf_png, format="PNG", optimize=True)
        st.download_button(
            label=trans.get(lang, "buttons.download_png"),
            data=buf_png.getvalue(),
            file_name=f"styled_{style_option.lower()}_{base_name}.png",
            mime="image/png",
            use_container_width=True,
            key=f"download_png_{base_name}_{style_option}"
        )
    
    with col_dl2:
        buf_jpg = io.BytesIO()
        styled_img.save(buf_jpg, format="JPEG", quality=95, optimize=True)
        st.download_button(
            label=trans.get(lang, "buttons.download_jpg"),
            data=buf_jpg.getvalue(),
            file_name=f"styled_{style_option.lower()}_{base_name}.jpg",
            mime="image/jpeg",
            use_container_width=True,
            key=f"download_jpg_{base_name}_{style_option}"  
        )
    

def display_comparison(original_img, styled_img, max_width=600):
    """
    Shows a comparison of the original and stylized images

    """
    col1, col2 = st.columns(2)
    
    orig_width = original_img.size[0]
    styled_width = styled_img.size[0]
    
    with col1:
        st.markdown(f"### {trans.get(st.session_state.language, 'main.original')}")
        if orig_width > max_width:
            st.image(original_img, width=max_width)
        else:
            st.image(original_img, width=orig_width)
    
    with col2:
        st.markdown(f"### {trans.get(st.session_state.language, 'main.result')}")
        if styled_width > max_width:
            st.image(styled_img, width=max_width)
        else:
            st.image(styled_img, width=styled_width)



# ===== Sidebar =====
with st.sidebar:
    st.markdown(f"### {trans.get(st.session_state.language, 'sidebar.language')}")
    
    language_options = trans.get_language_options()
    selected_lang_display = st.selectbox(
        "Language selection",
        options=list(language_options.keys()),
        index=list(language_options.values()).index(st.session_state.language)
        if st.session_state.language in language_options.values() else 0,
        label_visibility="collapsed"
    )
    
    selected_lang_code = language_options[selected_lang_display]
    if selected_lang_code != st.session_state.language:
        st.session_state.language = selected_lang_code
        st.rerun()
    
    st.markdown("---")
    
    st.markdown(f"### {trans.get(st.session_state.language, 'sidebar.upload.title')}")
    content_img = st.file_uploader(
        trans.get(st.session_state.language, "sidebar.upload.help"),
        type=['jpg', 'jpeg', 'png']
    )
    
    if content_img is not None:
        if ('last_uploaded' not in st.session_state or 
            st.session_state.last_uploaded != content_img.name):
            
            success, result = save_and_prepare_image(content_img, dataroot)
            if success:
                st.success(trans.get(
                    st.session_state.language,
                    "sidebar.upload.success",
                    filename=content_img.name
                ))
                for key, value in result.items():
                    st.session_state[key] = value
                st.session_state.last_uploaded = content_img.name
                st.session_state.process_requested = False 
            else:
                st.error(result)
    
    st.markdown("---")
    
    # Style choice
    st.markdown(f"### {trans.get(st.session_state.language, 'sidebar.style.title')}")
    
    localized_style_names = get_localized_style_names(st.session_state.language)
    selected_style_localized = st.selectbox(
        trans.get(st.session_state.language, "sidebar.style.help"),
        localized_style_names
    )
    
    english_style = get_english_style_from_localized(
        selected_style_localized,
        st.session_state.language
    )
    st.session_state.option = english_style
    
    # Style description
    style_description = trans.get_style_description(
        st.session_state.language,
        english_style
    )
    if style_description:
        st.info(f"**{selected_style_localized}**: {style_description}")
    
    st.markdown("---")
    
    # Process button
    process_disabled = not st.session_state.get('file_ready', False)
    
    if st.button(
        trans.get(st.session_state.language, "sidebar.process_button"),
        type="primary",
        use_container_width=True,
        disabled=process_disabled,
        key="process_btn" 
    ):
        if process_disabled:
            st.error(trans.get(st.session_state.language, "errors.no_image"))
        else:
            cleanup_results(results_dir)
            st.session_state.process_requested = True
            st.rerun()
# ===== About styles =====
with st.expander(trans.get(st.session_state.language, "styles_section.title")):
    
    localized_style_names = get_localized_style_names(st.session_state.language)
    
    style_tabs = st.tabs(localized_style_names)

    for idx, style_key in enumerate(["Monet", "Ukiyoe", "Cezanne", "Vangogh"]):
        with style_tabs[idx]:
            localized_name = trans.get_style_name(st.session_state.language, style_key)
            painter_text = get_painter_text(style_key, st.session_state.language)
            image_path = f"painters/{style_key}.jpg"
            if os.path.exists(image_path):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"## {localized_name}")
                    st.write(painter_text)
                with col2:
                    st.image(image_path, caption=style_key)
            else:
                st.markdown(f"## {localized_name}")
                st.write(painter_text)
# ===== Image process =====
if st.session_state.get('process_requested') and st.session_state.get('file_ready'):
    style_to_model = {
        "Monet": "style_monet_pretrained",
        "Ukiyoe": "style_ukiyoe_pretrained",
        "Cezanne": "style_cezanne_pretrained",
        "Vangogh": "style_vangogh_pretrained"
    }
    
    model_name = style_to_model.get(st.session_state.option, "style_monet_pretrained")
    
    model_checkpoint = os.path.join(checkpoints_dir, model_name, 'latest_net_G.pth')
    
    if not os.path.exists(model_checkpoint):
        st.warning(trans.get(
            st.session_state.language,
            "errors.model_not_found",
            model_name=model_name
        ))
    else:
        with st.spinner(trans.get(st.session_state.language, "main.processing")):
            try:
                current_filename = st.session_state.get('current_filename', '')
                if not current_filename:
                    st.error(trans.get(st.session_state.language, "errors.file_found_error")) #
                    st.session_state.process_requested = False
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text(trans.get(st.session_state.language, "progress.zero"))
                    progress_bar.progress(10)

                    input_file = os.path.join(dataroot, current_filename)
                    if not os.path.exists(input_file):
                        st.error(trans.get(st.session_state.language, "errors.file_found_error")) #
                        st.session_state.process_requested = False
                    try:
                        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                        from run_cyclegan_direct import run_test_directly
                        
                        status_text.text(trans.get(st.session_state.language, "progress.first"))
                        progress_bar.progress(30)
                        
                        success, message = run_test_directly(
                            dataroot=dataroot,
                            name=model_name,
                            checkpoints_dir=checkpoints_dir,
                            results_dir=results_dir,
                            cyclegan_dir=cyclegan_dir,
                            model='test',
                            no_dropout=True,
                            dataset_mode='single',
                            num_test=1,
                            load_size=256,
                            crop_size=256,
                            preprocess='none',
                            max_dataset_size=1000,
                            no_flip=True
                        )
                        
                        progress_bar.progress(70)
                        
                        if success:
                            status_text.text(trans.get(st.session_state.language, "progress.second"))
                            st.success(f"Результаты сохранены в: {message}")
                        else:
                            st.error(f"Ошибка CycleGAN: {message}")
                    except (ImportError, Exception) as e:
                        st.warning(trans.get(st.session_state.language, "errors.cyclegan_error"))#
                    progress_bar.progress(80)
                    status_text.text(trans.get(st.session_state.language, "progress.third"))
               
                    base_name = os.path.splitext(current_filename)[0]
                    st.session_state.base_name = base_name

                    final_dir = os.path.join(results_dir, model_name, 'test_latest', 'images')
                    fake_path = os.path.join(final_dir, f"{base_name}_fake.png")
                    
                    if os.path.exists(fake_path):
                        styled_image = Image.open(fake_path)
                        status_text.text(trans.get(st.session_state.language, "progress.fourth"))
                        progress_bar.progress(90)
                        
                        if hasattr(st.session_state, 'original_image') and st.session_state.original_image:
                            original_image = st.session_state.original_image
                            
                            if st.session_state.scale_info:
                                styled_image_resized = scale_back_to_original(styled_image, st.session_state.scale_info)
                            else:
                                styled_image_resized = styled_image
                            
                            st.session_state.styled_image = styled_image_resized
                            
                            progress_bar.progress(100)
                            status_text.text(trans.get(st.session_state.language, "progress.fifth"))
                            
                            display_images_and_downloads(
                                original_image,
                                styled_image_resized,
                                base_name,
                                st.session_state.option,
                                st.session_state.language
                            )
                            
                            st.success(trans.get(
                                st.session_state.language,
                                "main.success",
                                style=trans.get_style_name(st.session_state.language, st.session_state.option)
                            ))
                            st.balloons()
                            
                            st.session_state.process_requested = False
                        else:
                            st.session_state.process_requested = False
                    else:
                        
                        st.session_state.process_requested = False
                        
            except Exception as e:
                st.error(f"{trans.get(st.session_state.language, 'errors.processing_error')}: {str(e)}")
# =====Show images =====
elif st.session_state.original_image is not None and st.session_state.styled_image is not None:
    display_images_and_downloads(
        st.session_state.original_image,
        st.session_state.styled_image,
        st.session_state.base_name,
        st.session_state.option,
        st.session_state.language
    )

# ===== Examples =====
else:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {trans.get(st.session_state.language, 'main.example_original')}")
        imgs_dir = os.path.join(parent_dir, 'imgs')
        ex1_path = os.path.join(imgs_dir, 'example_real.jpg')
        
        if os.path.exists(ex1_path):
            ex1 = Image.open(ex1_path)
            st.image(ex1, width=500)
    
    with col2:
        st.markdown(f"### {trans.get(st.session_state.language, 'main.example_result')}")
        ex2_path = os.path.join(imgs_dir, 'example_fake.jpg')
        
        if os.path.exists(ex2_path):
            ex2 = Image.open(ex2_path)
            st.image(ex2, width=500)

# ===== About app =====
technologies = trans.get_nested(st.session_state.language, "app.about.technologies")
features = trans.get_nested(st.session_state.language, "app.about.features")

with st.expander(trans.get(st.session_state.language, "app.about.title")):
    st.subheader(trans.get(st.session_state.language, "app.about.tech"))
    for technologie in technologies:
        st.write(technologie)
    
    st.subheader(trans.get(st.session_state.language, "app.about.feat"))
    for feature in features:
        st.write(feature)

# ===== ФУТЕР =====
st.markdown("---")
st.caption(f"🎨 Style Transfer App • Language: {trans.get_language_display_name(st.session_state.language)}")
