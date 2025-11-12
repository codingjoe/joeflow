from django.core.management import BaseCommand

import joeflow.models


class Command(BaseCommand):
    help = "Render workflow graph to file."

    def add_arguments(self, parser):
        parser.add_argument(
            "workflow",
            nargs="*",
            type=str,
            help="List of workflows to render in the form app_label.workflow_name",
        )
        parser.add_argument(
            "-f",
            "--format",
            dest="format",
            type=str,
            choices=("svg", "pdf", "png"),
            default="svg",
            help="Output file format. Default: svg",
        )
        parser.add_argument(
            "-d",
            "--directory",
            dest="directory",
            type=str,
            help="Output directory. Default is current working directory.",
        )
        parser.add_argument(
            "-c",
            "--cleanup",
            dest="cleanup",
            action="store_true",
            help="Remove dot-files after rendering.",
        )

    def handle(self, *args, **options):
        workflows = options["workflow"]
        verbosity = options["verbosity"]
        file_format = options["format"]
        cleanup = options["cleanup"]
        directory = options.get("directory", None)

        workflows = [
            joeflow.models.get_workflow(s) for s in workflows
        ] or joeflow.models.get_workflows()

        for workflow in filter(None, workflows):
            if workflow != joeflow.models.Workflow:
                opt = workflow._meta
                if verbosity > 0:
                    self.stdout.write(
                        f"Rendering graph for '{opt.app_label}.{opt.model_name}'… ",
                        ending="",
                    )
                filename = f"{opt.app_label}_{workflow.__name__}".lower()
                graph = workflow.get_graph()
                graph.format = file_format
                graph.render(filename=filename, directory=directory, cleanup=cleanup)
                if verbosity > 0:
                    self.stdout.write("Done!", self.style.SUCCESS)
            else:
                self.stderr.write(
                    f"{workflow!r} is not a Workflow subclass", self.style.WARNING
                )
