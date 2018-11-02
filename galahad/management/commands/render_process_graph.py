from django.apps import apps
from django.core.management import BaseCommand

from galahad.models import Process


class Command(BaseCommand):
    help = "Render graphs for all processes as SVG files to the working directory"

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--format',
            dest='format', type=str,
            choices=('svg', 'pdf', 'png'),
            default='svg',
            help="Output file format. Default: svg"
        )
        parser.add_argument(
            '-d', '--directory',
            dest='directory', type=str,
            help="Output directory. Default is current working directory."
        )
        parser.add_argument(
            '-c', '--cleanup',
            dest='cleanup',
            action='store_true',
            help="Remove dot-files after rendering."
        )

    def handle(self, *args, **options):
        verbosity = options['verbosity']
        file_format = options['format']
        cleanup = options['cleanup']
        directory = options.get('directory', None)

        for model in apps.get_models():
            if issubclass(model, Process) and model != Process:
                opt = model._meta
                if verbosity > 0:
                    self.stdout.write("Rendering graph for '%s.%s'… " % (opt.app_label, opt.model_name), ending='')
                filename = '{app_label}_{model_name}'.format(
                    app_label=opt.app_label,
                    model_name=opt.model_name,
                )
                graph = model.get_graph()
                graph.format = file_format
                graph.render(filename=filename, directory=directory, cleanup=cleanup)
                if verbosity > 0:
                    self.stdout.write("Done!", self.style.SUCCESS)
