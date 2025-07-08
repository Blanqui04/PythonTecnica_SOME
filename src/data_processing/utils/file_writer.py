import os

def write_fragments(fragments, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for name, df in fragments.items():
        outpath = os.path.join(output_dir, f"{name}.json")
        df.to_json(outpath, orient='records', indent=2, force_ascii=False)
