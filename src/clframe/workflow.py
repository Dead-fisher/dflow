from argo.workflows.client import (
    ApiClient, Configuration,
    WorkflowServiceApi,
    V1alpha1Workflow,
    V1alpha1WorkflowCreateRequest,
    V1alpha1WorkflowSpec,
    V1ObjectMeta
)
from .steps import Steps

class Workflow:
    def __init__(self, name, steps=None, ip="127.0.0.1", port=2746):
        self.ip = ip
        self.port = port
        self.name = name
        if steps is not None:
            self.entrypoint = steps
        else:
            self.entrypoint = Steps(self.name)
        self.argo_templates = {}

    def add(self, step):
        self.entrypoint.add(step)

    def submit(self):
        self.handle_template(self.entrypoint)

        configuration = Configuration(host="https://%s:%s" % (self.ip, self.port))
        configuration.verify_ssl = False
        api_client = ApiClient(configuration)
        api_instance = WorkflowServiceApi(api_client)

        manifest = V1alpha1Workflow(
            metadata=V1ObjectMeta(generate_name=self.name + '-'),
            spec=V1alpha1WorkflowSpec(
                service_account_name='argo',
                entrypoint=self.entrypoint.name,
                templates=list(self.argo_templates.values())))

        api_response = api_instance.create_workflow(
            namespace='argo',
            body=V1alpha1WorkflowCreateRequest(workflow=manifest))
        print(api_response)
        return api_response

    def handle_template(self, template):
        if template.name not in self.argo_templates:
            if isinstance(template, Steps): # if the template is steps, handle involved templates
                argo_template, templates = template.convert_to_argo() # breadth first algorithm
                self.argo_templates[template.name] = argo_template
                for template in templates:
                    self.handle_template(template)
            else:
                self.argo_templates[template.name] = template.convert_to_argo()
