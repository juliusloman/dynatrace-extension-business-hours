from setuptools import setup, find_packages

setup(name="business_hours",
      version="0.0.1",
      description="Business hours EF2 extension",
      author="Dynatrace",
      packages=find_packages(),
      python_requires=">=3.10",
      include_package_data=True,
      install_requires=["dt-extensions-sdk", "croniter"],
      extras_require={"dev": ["dt-extensions-sdk[cli]"]},
      )
