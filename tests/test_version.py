from typer.testing import CliRunner 
from scm_config import __app_name__, __version__
from scm_config import cli 

test_runner = CliRunner()

def test_version():
    result = test_runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0 
    assert f"{__app_name__} - v{__version__}\n" in result.stdout 
    