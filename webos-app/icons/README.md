# WebOS App Icons

Folder ini untuk menyimpan icon files untuk WebOS app.

## Required Icons

1. **icon.png** - 80x80 pixels
   - App icon di launcher
   - Format: PNG with transparency
   
2. **largeIcon.png** - 130x130 pixels
   - Large app icon untuk detail page
   - Format: PNG with transparency

3. **bg.png** (Optional) - 1920x1080 pixels
   - Background image saat app loading
   - Format: PNG or JPEG

## Design Guidelines

### Icon Design
- **Simple dan clear**: Terlihat jelas di layar TV
- **High contrast**: Good visibility dari jarak jauh
- **Consistent branding**: Gunakan warna brand (Blue #3b82f6)
- **No text**: Icon harus jelas tanpa teks

### Recommended Style
- Modern flat design
- Signage/TV icon theme
- Blue and white color scheme
- Transparent background

## Create Icons

### Using Figma/Photoshop:
1. Create canvas: 130x130 px for largeIcon
2. Create canvas: 80x80 px for icon
3. Design icon dengan style yang sama
4. Export as PNG with transparency

### Using Online Tools:
- Canva: https://www.canva.com
- Figma: https://www.figma.com
- Photopea: https://www.photopea.com (free Photoshop alternative)

### Quick Icon Generation:
```bash
# Using ImageMagick (if installed)
# Create simple blue circle icon
convert -size 130x130 xc:none -fill '#3b82f6' -draw 'circle 65,65 65,10' largeIcon.png
convert -size 80x80 xc:none -fill '#3b82f6' -draw 'circle 40,40 40,5' icon.png
```

## Installation

Setelah icons dibuat, copy ke root webos-app folder:

```bash
# From icons folder
cp icon.png ../
cp largeIcon.png ../
cp bg.png ../ # if you have background
```

## Example Icons

Default icons menggunakan simple blue circles. 
Recommended untuk replace dengan design yang lebih professional.

### Suggested Icon Themes:
- 📺 TV/Monitor icon
- 📊 Digital signage icon
- 🎬 Media player icon
- 📱 Display screen icon

## Notes

- Icons currently use placeholders
- Replace dengan professional icons sebelum production
- Test icon visibility di TV screen dari jarak normal
