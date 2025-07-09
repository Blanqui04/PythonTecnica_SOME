from src.data_processing.data_transformer import DataTransformer

def transform_data_handler(client, project, datasheet_name):
    transformer = DataTransformer(client, project)
    return transformer.transform_datasheet(datasheet_name)