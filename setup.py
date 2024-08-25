from setuptools import setup, find_packages

setup(name="business_hours",
      version="0.0.15",
      description="Business hours EF2 extension",
      author="Dynatrace",
      packages=find_packages(),
      python_requires=">=3.10",
      include_package_data=True,
      install_requires=["dt-extensions-sdk", "croniter", "dacite", "icalendar", "recurring_ical_events", "requests", "charset_normalizer<3"],
      extras_require={"dev": ["dt-extensions-sdk[cli]"]},
      )
