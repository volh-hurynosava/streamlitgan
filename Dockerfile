FROM python:3.8-slim

RUN mkdir /app

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get update && \
    apt-get install -y git wget && \
    apt-get clean


RUN git clone https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix

RUN chmod +x ./pytorch-CycleGAN-and-pix2pix/scripts/download_cyclegan_model.sh && \
    ./pytorch-CycleGAN-and-pix2pix/scripts/download_cyclegan_model.sh style_monet && \
    ./pytorch-CycleGAN-and-pix2pix/scripts/download_cyclegan_model.sh style_ukiyoe && \
    ./pytorch-CycleGAN-and-pix2pix/scripts/download_cyclegan_model.sh style_cezanne && \
    ./pytorch-CycleGAN-and-pix2pix/scripts/download_cyclegan_model.sh style_vangogh     

COPY . /app
    

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]