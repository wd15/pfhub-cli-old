"""`convert` function to convert between meta.yaml and pfhub.yaml
formats.

"""

import tempfile
from shutil import make_archive
import os
import pathlib
import shutil

from dotwiz import DotWiz
from toolz.curried import pipe, dissoc, groupby, get, merge
from toolz.curried import map as map_

from .func import fullmatch, read_yaml, render, get_data_from_yaml, sequence, curry
from .zenodo import zenodo_to_meta


def convert(url):
    """Convert a PFHub record between different storage versions.

    Take a PFHub records stored at a URL and convert it to another
    version of PFHub storage.

    Args:
      url: the url of the PFHub record file

    Returns:
      returns a link to a file or link to a tarball of files

    Read a Zenodo DOI data and return a meta.yaml file as a string.

    >>> print(convert("https://doi.org/10.5281/zenodo.7474506"))
    ---
    name: fipy_1a_10.5281/zenodo.7474506
    ...
            as: y
    <BLANKLINE>

    Read a meta.yaml and output a pfhub.yaml file ready for upload to
    Zenodo. The file is dumped in a file called pfhub.zip.

    >>> yaml_file = getfixture('yaml_data_file')
    >>> path = convert(str(yaml_file))
    >>> print(os.path.split(path)[1])
    pfhub.zip
    >>> os.remove(path)

    Fail if given a URL without `meta.yaml` at the end or not a Zenodo
    DOI link.

    >>> convert("https://notcorrect.com")
    Traceback (most recent call last):
    ...
    RuntimeError: "https://notcorrect.com" conversion is not yet implemented

    """

    match_zenodo = fullmatch(r"https://doi.org/\d{2}.\d{4}/zenodo.\d{7}")
    match_meta = fullmatch(r".*/meta.yaml")

    if match_zenodo(url):
        return zenodo_to_meta(url)

    if match_meta(url):
        return meta_to_zenodo(url)

    raise RuntimeError(f'"{url}" conversion is not yet implemented')


@curry
def get_timeseries_info(meta_yaml, item):
    """Return the time series data from a meta.yaml for a phfub.yaml.

    Args:
      meta_yaml: the meta.yaml string
      item: a data item from `{benchmark_id}_data.yaml` file in the
        `templates/` directory

    Returns:
      a dotwizzed dict of the necessary date to build the data itme
      for pfhub.yaml

    Using some test data generate the combined data structure output
    from `get_timeseries_info`.

    >>> meta_yaml = DotWiz(
    ...     data=[DotWiz(name='free_energy', values=[DotWiz(x=0, y=1), DotWiz(x=1, y=2)])]
    ... )
    >>> item = DotWiz(name='free_energy', schema=DotWiz(
    ...     name='free_energy_1.csv', format='csv', columns=DotWiz(time='x', free_energy='y')
    ... ))
    >>> get_timeseries_info(meta_yaml, item)
    DotWiz(dataframe=   x  y     data_set
    0  0  1  free_energy
    1  1  2  free_energy, name='free_energy_1.csv', format='csv', columns=[DotWiz(name='x'), DotWiz(name='y')])

    """  # pylint: disable=line-too-long # noqa: E501
    return pipe(
        [item.name],
        get_data_from_yaml(keys=["x", "y"], yaml_data=meta_yaml),
        lambda x: x.rename(item.schema.columns),
        lambda x: dotwiz(
            {
                "dataframe": x,
                "name": item.schema.name,
                "format": item.schema.format,
                "columns": list(
                    map_((lambda x: {"name": x}), item.schema.columns.values())
                ),
            }
        ),
    )


dotwiz = lambda x: DotWiz(**x)


def meta_to_zenodo(url):
    """Convert a meta.yaml link to pfhub.json ready for upload to Zenodo

    Args:
      url: the url of meta.yaml file

    Returns:
      the path to the pfhub.zip bundle which includes the pfhub.yaml
      and other files to upload to Zenodo

    >>> yaml_file = getfixture('yaml_data_file')
    >>> path = meta_to_zenodo(str(yaml_file))
    >>> print(os.path.split(path)[1])
    pfhub.zip
    >>> os.remove(path)


    """
    return pipe(url, read_yaml, dotwiz, get_file_strings, bundle("pfhub"))


@curry
def bundle(zipname, string_dict, path="."):
    """Bundle strings into a zip file

    Args:
      zipname: the name of the zip file (not including the extension)
      string_dict: a dictionary of strings with filenames as keys
      path: path to place {zipname}.zip

    Returns:
      the path to the bundled filename

    Test by writing and reading a single file `a.txt`

    >>> tmp = getfixture('tmp_path')
    >>> out = bundle('file', {'a.txt' : 'hello'}, path=tmp)
    >>> shutil.unpack_archive(out, tmp)
    >>> print(open((tmp / 'a.txt'), 'r').read())
    hello

    """

    @curry
    def write(dir_, item):
        with open(dir_ + f"/{item[0]}", "w", encoding="utf-8") as fstream:
            fstream.write(item[1])

    write_files = lambda s, d: list(map_(write(d), s.items()))

    tmpdir = tempfile.mkdtemp()

    write_files(string_dict, tmpdir)

    zip_path = make_archive(os.path.join(path, f"{zipname}"), "zip", tmpdir)

    shutil.rmtree(tmpdir)

    return zip_path


def get_file_strings(meta_yaml):
    """Build the structures for generating pfhub.yaml from meta.yaml

    Args:
      meta_yaml: wizdot version of meta.yaml

    Returns:
      a dictionary of files and contents for wring to disk including
      the pfhub.yaml and necessary data fils

    >>> yaml_file = str(getfixture('yaml_data_file'))
    >>> out = get_file_strings(dotwiz(read_yaml(yaml_file)))

    The keys are files.

    >>> print(out.keys())
    dict_keys(['pfhub.yaml', 'free_energy_1a.csv'])

    The values are the file contents

    >>> print(out['free_energy_1a.csv'])
    x,y,data_set
    0.0,0.0,free_energy
    1.0,1.0,free_energy
    <BLANKLINE>

    """
    get_schema_data = sequence(
        lambda x: (
            pathlib.Path(__file__).parent.resolve()
            / "templates"
            / f"{x.benchmark.id}_data.yaml"
        ),
        read_yaml,
    )

    pfhub_yaml_func = sequence(
        map_(lambda x: dissoc(x, "dataframe")),
        list,
        render_pfhub_schema(
            meta_yaml,
            get_data_from_yaml(["run_time"], ["wall_time", "sim_time"], meta_yaml),
            get_data_from_yaml(["memory_usage"], ["value"], meta_yaml),
        ),
    )

    helper = lambda x: (x.name, x.dataframe.to_csv(index=False))

    return pipe(
        meta_yaml,
        get_schema_data,
        groupby(lambda x: x["schema"]["type"]),
        get("file_timeseries"),
        map_(dotwiz),
        map_(get_timeseries_info(meta_yaml)),
        list,
        lambda x: merge({"pfhub.yaml": pfhub_yaml_func(x)}, dict(map_(helper, x))),
    )


@curry
def render_pfhub_schema(data, time_data, memory_data, timeseries):
    """Render the pfhub.yaml

    Args:
      data: the wizdotted meta.yaml file data
      time_data: a Pandas dataframe of the run_time data
      memory_usage: a Pandas dataframe of the memory_usage data
      timeseries: a set of data dictionaries with the contents of all
        data categorized as timeseries data

    Returns:
      the rendered pfhub.yaml as a string

    >>> yaml_data = dotwiz(read_yaml(str(getfixture('yaml_data_file'))))
    >>> import pandas
    >>> out = render_pfhub_schema(
    ...     yaml_data,
    ...     pandas.DataFrame(dict(wall_time=[1], sim_time=[1])),
    ...     pandas.DataFrame(dict(value=[1])),
    ...     timeseries=[DotWiz(name='name', format='csv', columns=[DotWiz(name='x')])]
    ... )
    >>> print(*out.split('\\n')[:3], sep='\\n')
    ---
    id: https://github.com
    benchmark_problem: 1a
    >>> print(*out.split('\\n')[-3:], sep='\\n')
      memory_in_kb: 1
      time_in_s: 1
    <BLANKLINE>

    """

    return render(
        "pfhub.schema",
        {
            "problem": data.benchmark.id,
            "benchmark_version": data.benchmark.version,
            "summary": data.metadata.summary,
            "contributors": [
                {
                    "id": "github:" + data.metadata.author.github_id,
                    "name": data.metadata.author.first
                    + " "
                    + data.metadata.author.last,
                    "email": data.metadata.author.email,
                }
            ],
            "framework": [{"name": data.metadata.implementation.name}],
            "implementation_url": data.metadata.implementation.repo.url,
            "date": data.metadata.timestamp,
            "wall_time": time_data.wall_time.iloc[-1],
            "memory": memory_data.value.iloc[-1],
            "fictive_time": time_data.sim_time.iloc[-1],
            "hardware": [
                {
                    "architecture": data.metadata.hardware.cpu_architecture,
                    "cores": data.metadata.hardware.cores,
                    "nodes": data.metadata.hardware.nodes,
                }
            ],
            "file_timeseries": timeseries,
        },
    )
