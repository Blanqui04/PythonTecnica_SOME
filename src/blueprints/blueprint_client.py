class BlueprintFactory:
    @staticmethod
    def create_parser(client_type):
        if client_type == 'client_a':
            return ClientAParser()
        elif client_type == 'client_b':
            return ClientBParser()
        else:
            return DefaultParser()