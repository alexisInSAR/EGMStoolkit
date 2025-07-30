from PIL import Image
import qrcode
from qrcode.image.styledpil import StyledPilImage

## Create the code
qr = qrcode.QRCode(version=10,box_size=27,error_correction=qrcode.constants.ERROR_CORRECT_H)
data = "https://github.com/alexisInSAR/EGMStoolkit"
qr.add_data(data)
qr.make(fit=True)
img = qr.make_image(image_factory=StyledPilImage)

## Save
img.save("QRcode_EGMSToolkit.png")