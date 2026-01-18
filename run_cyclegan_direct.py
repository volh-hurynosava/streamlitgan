import sys
import os
from pathlib import Path
import torch

def run_test_directly(dataroot, name, checkpoints_dir, results_dir, cyclegan_dir, **kwargs):
    """
    Runs CycleGAN test directly without subprocess
    """
    try:
        sys.path.insert(0, cyclegan_dir)
        try:
            from options.test_options import TestOptions
            from data import create_dataset
            from models import create_model
            from util.visualizer import save_images
            from util import html
        except ImportError as e:
            raise
            
        class MockArgs:
            def __init__(self):
                self.dataroot = dataroot
                self.name = name
                self.model = kwargs.get('model', 'test')
                self.no_dropout = kwargs.get('no_dropout', True)
                self.checkpoints_dir = checkpoints_dir
                self.results_dir = results_dir
                self.dataset_mode = kwargs.get('dataset_mode', 'single')
                self.num_test = kwargs.get('num_test', 1)
                self.load_size = kwargs.get('load_size', 256)
                self.crop_size = kwargs.get('crop_size', 256)
                self.preprocess = kwargs.get('preprocess', 'none')
                self.max_dataset_size = kwargs.get('max_dataset_size', 1000)
                self.no_flip = kwargs.get('no_flip', True)
                self.gpu_ids = '-1'
                self.ngf = 64
                self.ndf = 64
                self.netG = 'resnet_9blocks'
                self.netD = 'basic'
                self.norm = 'instance'
                self.init_type = 'normal'
                self.init_gain = 0.02
                self.no_lsgan = False
                self.pool_size = 50
                self.epoch = 'latest'
                self.verbose = False
                self.suffix = ''
                self.model_suffix = ''
                self.aspect_ratio = 1.0
                self.phase = 'test'
                self.eval = False
                self.num_threads = 0
                self.batch_size = 1
                self.serial_batches = True
                self.direction = 'AtoB'
                self.input_nc = 3
                self.output_nc = 3
                self.display_winsize = 256
                self.display_id = -1
                self.display_server = "http://localhost"
                self.display_env = 'main'
                self.display_port = 8097
                self.update_html_freq = 1000
                self.print_freq = 100
                self.no_html = True
                self.isTrain = False
                self.load_iter = 0
                self.continue_train = False

        opt = MockArgs()
        opt.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        try:
            dataset = create_dataset(opt)
        except Exception as e:
            raise
            
        try:
            model = create_model(opt)
            model.setup(opt)
        except Exception as e:
            raise

        web_dir = Path(opt.results_dir) / opt.name / f"{opt.phase}_{opt.epoch}"
        if opt.load_iter > 0:
            web_dir = Path(f"{web_dir}_iter{opt.load_iter}")

        web_dir.mkdir(parents=True, exist_ok=True)

        webpage = html.HTML(web_dir, f"Experiment = {opt.name}, Phase = {opt.phase}, Epoch = {opt.epoch}")

        if opt.eval:
            model.eval()

        for i, data in enumerate(dataset):
            if i >= opt.num_test:
                break

            model.set_input(data)
            model.test()
            visuals = model.get_current_visuals()
            img_path = model.get_image_paths()

            if i % 5 == 0:

            save_images(webpage, visuals, img_path, aspect_ratio=opt.aspect_ratio, width=opt.display_winsize)

        webpage.save()

        images_dir = web_dir / "images"
        return True, str(images_dir)

    except ImportError as e:
        error_msg = f"❌ CycleGAN import error: {e}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return False, error_msg
    except Exception as e:
        error_msg = f"❌ CycleGAN execution error: {e}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return False, error_msg
