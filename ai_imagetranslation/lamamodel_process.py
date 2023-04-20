# import torch
# import cv2 ,os
# import numpy as np
# pad_mod = 8
# pad_to_square = False
# min_size = None
import os 
import requests
IMAGE_TRANSLATE_URL = os.getenv('IMAGE_TRANSLATE_URL')
import numpy as np
# model = torch.jit.load(model_path, map_location="cpu")
# model = model.to('cpu')

# def ceil_modulo(x, mod):
#     if x % mod == 0:
#         return x
#     return (x // mod + 1) * mod

# def norm_img(np_img):
#     if len(np_img.shape) == 2:
#         np_img = np_img[:, :, np.newaxis]
#     np_img = np.transpose(np_img, (2, 0, 1))
#     np_img = np_img.astype("float32") / 255
#     return np_img


# def pad_img_to_modulo(img,mod,square=False,min_size=None):
#     if len(img.shape) == 2:
#         img = img[:, :, np.newaxis]
#     height, width = img.shape[:2]
#     out_height = ceil_modulo(height, mod)
#     out_width = ceil_modulo(width, mod)
#     return np.pad(
#         img,
#         ((0, out_height - height), (0, out_width - width), (0, 0)),
#         mode="symmetric",)

# @torch.no_grad()
# def forward(image,mask):
#     image = norm_img(image)
#     mask = norm_img(mask)
#     mask = (mask > 0) * 1
#     image = torch.from_numpy(image).unsqueeze(0).to('cpu')
#     mask = torch.from_numpy(mask).unsqueeze(0).to('cpu')
#     inpainted_image = model(image, mask)
#     cur_res = inpainted_image[0].permute(1, 2, 0).detach().cpu().numpy()
#     cur_res = np.clip(cur_res * 255, 0, 255).astype("uint8")
#     cur_res = cv2.cvtColor(cur_res, cv2.COLOR_RGB2BGR)
#     return cur_res

def inpaint_image(im,msk):
    headers = {} 
    payload={}
    files=[
    ('image',('',open(im,'rb'),'')),
    ('mask',('',open(msk,'rb'),''))
    ]
    response = requests.request("POST", IMAGE_TRANSLATE_URL, headers=headers, data=payload, files=files)
    arr = np.frombuffer(response.content, dtype=np.uint8)
    
    # origin_height, origin_width = im.shape[:2]
    # pad_image = pad_img_to_modulo(im, mod=pad_mod, square=pad_to_square, min_size=min_size)
    # pad_mask = pad_img_to_modulo(msk, mod=pad_mod, square=pad_to_square, min_size=min_size)
    # res = forward(pad_image,pad_mask)
    # result = res[0:origin_height, 0:origin_width, :]
    # original_pixel_indices = msk < 127
    # result[original_pixel_indices] = im[:, :, ::-1][original_pixel_indices]
    return arr