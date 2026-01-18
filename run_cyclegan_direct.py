import torch

def run_test_directly(dataroot, name, checkpoints_dir, results_dir, cyclegan_dir, **kwargs):
    """
    Запускает CycleGAN test напрямую без subprocess
    
    Args:
        dataroot: путь к данным
        name: имя модели
        checkpoints_dir: путь к чекпоинтам
        results_dir: путь для результатов
        cyclegan_dir: путь к папке Cyclegan
        **kwargs: дополнительные параметры
    """
    try:
        print(f"📁 Текущая директория: {os.getcwd()}")
        print(f"📁 CycleGAN директория: {cyclegan_dir}")
        print(f"📁 CycleGAN существует: {os.path.exists(cyclegan_dir)}")

        # Добавляем путь к CycleGAN
        sys.path.insert(0, cyclegan_dir)

        # Проверяем что можем импортировать
        print("🔍 Проверяем импорт модулей CycleGAN...")

        # Импортируем модули CycleGAN
        try:
            from options.test_options import TestOptions
            from data import create_dataset
            from models import create_model
            from util.visualizer import save_images
            from util import html

            print("✅ Модули CycleGAN успешно импортированы")
        except ImportError as e:
            print(f"❌ Error importing modules CycleGAN: {e}")
            print(f"{cyclegan_dir}:")
            print(f"❌ Ошибка импорта модулей CycleGAN: {e}")
            # Показываем что есть в директории
            print(f"Содержимое {cyclegan_dir}:")
            if os.path.exists(cyclegan_dir):
                for item in os.listdir(cyclegan_dir):
                    print(f"  - {item}")
            raise
        

        print(f"🚀 Запускаем CycleGAN с параметрами:")
        print(f"  dataroot: {dataroot}")
        print(f"  name: {name}")
        print(f"  checkpoints_dir: {checkpoints_dir}")
        print(f"  results_dir: {results_dir}")
        print(f"  cyclegan_dir: {cyclegan_dir}")
        

        # Создаем объект опций вручную
        class MockArgs:
            def __init__(self):
@@ -77,58 +101,85 @@ def __init__(self):
                self.isTrain = False
                self.load_iter = 0
                self.continue_train = False
                

        # Создаем опции
        opt = MockArgs()
        opt.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
 

        print(f"🔧 Опции настроены, создаем dataset...")

        # Создаем датасет
        try:
            dataset = create_dataset(opt)
            print(f"✅ Датасет создан, количество элементов: {len(dataset)}")
        except Exception as e:
            print(f"❌ Error creating dataset: {e}")
            print(f"❌ Ошибка при создании датасета: {e}")
            raise

        print(f"📊 Датасет создан, создаем модель...")

        # Создаем модель
        try:
            model = create_model(opt)
            model.setup(opt)
            print(f"✅ The model is created and configured")
            print(f"✅ Модель создана и настроена")
        except Exception as e:
            print(f"❌ Error creating model: {e}")
            print(f"❌ Ошибка при создании модели: {e}")
            raise
        

        print(f"🎯 Модель создана и настроена")

        # Создаем веб-сайт для результатов
        web_dir = Path(opt.results_dir) / opt.name / f"{opt.phase}_{opt.epoch}"
        if opt.load_iter > 0:
            web_dir = Path(f"{web_dir}_iter{opt.load_iter}")
   

        # Создаем директорию если не существует
        web_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Создаем директорию для результатов: {web_dir}")

        webpage = html.HTML(web_dir, f"Experiment = {opt.name}, Phase = {opt.phase}, Epoch = {opt.epoch}")

        # Устанавливаем модель в eval mode если нужно
        if opt.eval:
  
            model.eval()

        print(f"🎨 Начинаем обработку изображений...")

        # Обрабатываем изображения
        for i, data in enumerate(dataset):
            if i >= opt.num_test:
                break
                

            model.set_input(data)
            model.test()
            visuals = model.get_current_visuals()
            img_path = model.get_image_paths()
            

            if i % 5 == 0:
                
                print(f"🖼️  Обрабатываем изображение ({i:04d})-е... {img_path}")

            save_images(webpage, visuals, img_path, aspect_ratio=opt.aspect_ratio, width=opt.display_winsize)

        # Сохраняем HTML
        webpage.save()
   

        print(f"✅ CycleGAN выполнен успешно!")
        print(f"📂 Результаты сохранены в: {web_dir}")

        # Возвращаем путь к результатам
        images_dir = web_dir / "images"
        return True, str(images_dir)
        

    except ImportError as e:
        error_msg = f"❌ CycleGAN import error: {e}"
        error_msg = f"❌ Ошибка импорта CycleGAN: {e}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return False, error_msg
    except Exception as e:
        error_msg = f"❌ CycleGAN execution error: {e}"
        error_msg = f"❌ Ошибка выполнения CycleGAN: {e}"
        print(error_msg)
        import traceback
