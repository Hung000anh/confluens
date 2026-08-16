from PIL import Image
import collections

img = Image.open('test_mpf.png').convert('RGB')
colors = img.getcolors(maxcolors=100000)
# Check if white (#ffffff) or red (#ef5350) is present
has_white = any(c[1] == (255, 255, 255) for c in colors)
has_red = any(c[1] == (239, 83, 80) for c in colors)
print(f"Has White: {has_white}")
print(f"Has Red: {has_red}")
