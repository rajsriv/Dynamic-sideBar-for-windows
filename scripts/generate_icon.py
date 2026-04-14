import os
from PIL import Image, ImageDraw

def create_icon():
                                                        
    size = 256
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    bar_width = 180
    bar_height = 40
    spacing = 25
    radius = 20
    
    x0 = (size - bar_width) // 2
    y_start = (size - (3 * bar_height + 2 * spacing)) // 2
    
    for i in range(3):
        y = y_start + i * (bar_height + spacing)
                                        
        draw.rounded_rectangle(
            [x0, y, x0 + bar_width, y + bar_height],
            radius=radius,
            fill=(0, 0, 0, 255)
        )
    
    assets_dir = 'assets'
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    png_path = os.path.join(assets_dir, 'icon.png')
    img.save(png_path)
    
    ico_path = os.path.join(assets_dir, 'icon.ico')
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"Icon generated at {ico_path}")

if __name__ == "__main__":
    create_icon()
