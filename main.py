import subprocess
import os
import sys
import streamlit as st
from PIL import Image

subdirectory = "pytorch-CycleGAN-and-pix2pix"
if(not (os.getcwd()).endswith(subdirectory)):
  os.chdir(subdirectory)
  print(f"Changed directory to '{os.getcwd()}'.")

parent_dir = os.path.dirname(os.path.abspath(os.getcwd()))
script_path = os.path.abspath('test.py')
dataroot = os.path.abspath('datasets/test/testA')
results_dir = os.path.abspath('results')
model_name = "style_monet_pretrained"
try:
    os.makedirs(dataroot, exist_ok=True)
except OSError as error:
    print(f"Error creating directory '{dataroot}': {error}")

st.set_page_config(layout="wide", page_title="Image Style Transfer")
st.header("Transfer style to your image") 
st.subheader("Try upload image and get stylized image. Look at the example of a style transferred image")
on = st.toggle("Learn more about painters")
if on:
    painter = st.selectbox("Which painter or  would you like to read about?",("Monet", "Ukiyoe", "Cezanne", "Vangogh"))
    with open(parent_dir+"/painters/"+painter+".txt", 'r') as file:
        content = file.read()
        st.markdown(content)
    paint = Image.open(parent_dir+"/painters/"+painter+".jpg")
    st.image(paint,use_column_width=True)
        

st.sidebar.write("## Upload and download :gear:")

content_img = st.sidebar.file_uploader("Upload jpg image", type = ['jpg'])


if content_img is not None:
  with open(os.path.join(dataroot,content_img.name),"wb") as f:
     f.write(content_img.getbuffer())

option = st.sidebar.selectbox(
    "Which style would you like?",
    ("Monet", "Ukiyoe", "Cezanne", "Vangogh"))

if option == "Monet":
  model_name = "style_monet_pretrained"
elif option == "Ukiyoe" :
  model_name = "style_ukiyoe_pretrained"
elif option == "Cezanne":
  model_name = "style_cezanne_pretrained"
elif option ==  "Vangogh" :
  model_name = "style_vangogh_pretrained"

command = [
     sys.executable, script_path,
    '--dataroot', dataroot,
    '--name', model_name,
    '--model', 'test',
    '--no_dropout',
    '--gpu_ids', '-1',
    ]

col1, col2 = st.columns(2)
   
if st.sidebar.button('Create image'):
      with st.spinner('Creating image...'):
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        final_dir = results_dir+"/"+ model_name+'/test_latest/images/'
        final_img = content_img.name.rsplit('.jpg', 1)[0]
        real_img = final_img +'_real.png'
        final_img = final_img +'_fake.png'
        image1 = Image.open(os.path.join(final_dir, real_img))
        image2 = Image.open(os.path.join(final_dir, final_img))
        col1.write("Your Image :camera:")
        col1.image(image1, use_column_width=True)
        col2.write("Result Image :art:")
        col2.image(image2,use_column_width=True)
else:
   col1.write("Your Image :camera:")
   ex1 = Image.open(os.path.join(parent_dir,'imgs','example_real.jpg'))
   col1.image(ex1, use_column_width=True)

   ex2 = Image.open(os.path.join(parent_dir,'imgs','example_fake.jpg'))
   col2.write("Result Image :art:")
   col2.image(ex2,use_column_width=True)
   
        
      
       