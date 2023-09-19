import littlecms as lc
import PIL
from PIL import Image
import numpy as np
from functools import lru_cache
class rgbImage(object):
    def __init__(self,image):
        self._image = image

    image = property(lambda self : self._image)
    r = property(lambda self : self._image.getchannel("R"))
    g = property(lambda self : self._image.getchannel("G"))
    b = property(lambda self : self._image.getchannel("B"))
    show = property(lambda self: self._image.show())

class cmykImage(object):
    def __init__(self,image):
        self._image = image

    image = property(lambda self : self._image)
    c = property(lambda self : self._image.getchannel("C"))
    m = property(lambda self : self._image.getchannel("M"))
    y = property(lambda self : self._image.getchannel("Y"))
    k = property(lambda self : self._image.getchannel("K"))
    show = property(lambda self: self._image.show())

def cmyk_from_PIL(image:PIL.Image)->cmykImage:
    return cmykImage(image)

def cmyk_from_directory(path:str)->cmykImage:
    return cmykImage(PIL.Image.open(path))

def rgb_from_PIL(image:PIL.Image)->cmykImage:
    return rgbImage(image)

def rgb_from_directory(path:str)->cmykImage:
    return rgbImage(PIL.Image.open(path))

 
@lru_cache(maxsize=128)
def convertImage(image_path)->PIL.Image:
    image = Image.open(image_path)
    conversion_tpye ="RGB2CMYK"
    (SRC_COLOR_TYPE,DST_COLOR_TYPE) = conversion_tpye.split("2")

    cmsColorType = {"RGB":lc.TYPE_RGB_8 , "CMYK":lc.TYPE_CMYK_8}
    cmsColorChannel = {"RGB":3 , "CMYK":4}

    ctxt = lc.cmsCreateContext(None, None)
    white = lc.cmsD50_xyY()    # Set white point for D50
    dst_profile = lc.cmsOpenProfileFromFile('ai_canvas/ICC_profile/USWebCoatedSWOP.icc', 'r')
    src_profile = lc.cmsOpenProfileFromFile('ai_canvas/ICC_profile/sRGB.icm', 'r') # cmsCreate_sRGBProfile() 
    transform = lc.cmsCreateTransform(src_profile, cmsColorType[SRC_COLOR_TYPE], dst_profile, cmsColorType[DST_COLOR_TYPE],
                                lc.INTENT_RELATIVE_COLORIMETRIC, lc.cmsFLAGS_NOCACHE)

    n_pixels = image.size[0]
    in_comps = cmsColorChannel[SRC_COLOR_TYPE]
    out_comps = cmsColorChannel[DST_COLOR_TYPE]
    n_rows = 16

    in_Array = lc.uint8Array(in_comps * n_pixels * n_rows)
    out_Array = lc.uint8Array(out_comps * n_pixels * n_rows)

    outImage = PIL.Image.new(DST_COLOR_TYPE, image.size, 'white')
    in_row = PIL.Image.new(SRC_COLOR_TYPE, (image.size[0], n_rows), 'white')
    out_row = PIL.Image.new(DST_COLOR_TYPE, (image.size[0], n_rows), 'white')
    out_b = bytearray(n_pixels * n_rows * out_comps)
    row = 0

    while row < image.size[1] :
        in_row.paste(image, (0, -row))
        pix = np.array(in_row)
        data_in = in_row.tobytes('raw')
        
        j = in_comps * n_pixels * n_rows

        for i in range(j):
            in_Array[i] = data_in[i]

        lc.cmsDoTransform(transform, in_Array, out_Array, n_pixels * n_rows)

        for j in out_Array :
            out_b[j] = out_Array[j]       

        out_row = PIL.Image.frombytes(DST_COLOR_TYPE, in_row.size, bytes(out_b))
        outImage.paste(out_row, (0, row))
        row += n_rows

    # if DST_COLOR_TYPE == "RGB":
    #     return rgb_from_PIL(outImage)

    if DST_COLOR_TYPE == "CMYK":
        return cmyk_from_PIL(outImage)
    
    raise Exception("Undefinied Color type of Image.Avaliable types RBG  & CMYK")