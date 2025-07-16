# src/services/data_processing_orchestrator.py

import logging
from src.data_processing.pipeline_manager import DataProcessingPipeline
from src.data_processing.data_transformer import DataTransformer
from src.exceptions import TransformationError

logger = logging.getLogger(__name__)

class DataProcessingOrchestrator:
    def __init__(self):
        self.pipeline = DataProcessingPipeline()

    def process_and_transform(self, client: str, ref_project: str, mode: str = 'kop'):
        logger.info(f"Starting full process for client={client}, ref_project={ref_project}, mode={mode}")
        
        # Step 1: Process with pipeline
        result, message = self.pipeline.process_project(client, ref_project, mode)

        if not result:
            logger.error(f"Pipeline processing failed: {message}")
            return None, f"Pipeline failed: {message}"

        # Step 2: Transform with DataTransformer
        datasheet_name = f"datasheet_{client}_{ref_project}"
        try:
            transformer = DataTransformer(client, ref_project)
            transform_result = transformer.transform_datasheet(datasheet_name)
            logger.info("Transformation successful")
            return transform_result, "Processing and transformation successful"
        except TransformationError as te:
            logger.exception("Transformation error")
            return None, f"Transformation error: {te}"
        except Exception as e:
            logger.exception("Unexpected error during transformation")
            return None, f"Unexpected error: {e}"
