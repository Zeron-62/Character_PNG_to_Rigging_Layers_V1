from pathlib import Path
from PIL import Image
import zipfile


def _safe(name: str, fallback='layer'):
    s=''.join(c if c.isalnum() or c in '-_' else '_' for c in (name or '')).strip('_')
    return s or fallback


def _walk(layers, prefix=''):
    for i, layer in enumerate(layers):
        name=(prefix + (layer.name or f'layer_{i:02d}')).strip()
        yield layer, name
        if layer.is_group():
            yield from _walk(layer, name+'__')


def inspect_psd(psd_path: Path):
    from psd_tools import PSDImage
    psd=PSDImage.open(psd_path)
    items=[]
    for idx,(layer,path_name) in enumerate(_walk(psd)):
        try: bbox=tuple(int(v) for v in layer.bbox)
        except Exception: bbox=(0,0,0,0)
        items.append({
            'id': idx,
            'name': layer.name or f'layer_{idx:02d}',
            'path_name': path_name,
            'group': bool(layer.is_group()),
            'visible': bool(layer.visible),
            'bbox': bbox,
            'width': max(0,bbox[2]-bbox[0]),
            'height': max(0,bbox[3]-bbox[1]),
        })
    return {'width': psd.width, 'height': psd.height, 'layer_count': len(items), 'layers': items}


def render_layer(psd_path: Path, layer_id: int):
    from psd_tools import PSDImage
    psd=PSDImage.open(psd_path)
    pairs=list(_walk(psd))
    if layer_id<0 or layer_id>=len(pairs): raise IndexError('Layer not found')
    layer,_=pairs[layer_id]
    if layer.is_group():
        im=layer.composite()
    else:
        im=layer.topil()
    if im is None: raise ValueError('Layer has no renderable pixels')
    return im.convert('RGBA')


def export_layers(psd_path: Path, destination: Path):
    from psd_tools import PSDImage
    psd=PSDImage.open(psd_path)
    destination.mkdir(parents=True, exist_ok=True)
    w,h=psd.size
    results=[]
    for i,(layer,path_name) in enumerate(_walk(psd)):
        if layer.is_group(): continue
        try:
            im=layer.topil()
            full=Image.new('RGBA',(w,h),(0,0,0,0))
            if im:
                x0,y0,x1,y1=layer.bbox
                full.alpha_composite(im.convert('RGBA'),(x0,y0))
            path=destination/(_safe(path_name,f'layer_{i:02d}')+'.png')
            full.save(path)
            results.append(path)
        except Exception:
            continue
    return results


def export_zip(psd_path: Path, destination: Path):
    files=export_layers(psd_path,destination)
    zip_path=destination.parent/(destination.name+'.zip')
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for f in files: z.write(f,f.name)
    return zip_path, files
