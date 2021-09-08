# image_viewer_mk2
Simple image viewer

## Dependencies

**Non-standard libraries**: happy

**Standard libraries**: PIL, matplotlib, numpy, (optional: PyTorch, pywin32)

## Usage

From python script
```
import image_viewer_mk2.app as imv

img = np.zeros((height, width, channels))
imv.main(image=img)
```

From command line
```
> python -m image_viewer_mk2.app [filename]
```
