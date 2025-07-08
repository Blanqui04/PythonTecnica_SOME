class BlueprintManager:
    def __init__(self):
        self.factory = BlueprintFactory()
    
    def process_blueprint(self, blueprint_path, client_type):
        parser = self.factory.create_parser(client_type)
        return parser.parse(blueprint_path)