# import os

# import yaml
# from chime_frb_api import get_logger

# logger = get_logger()

# _SITE_OPTIONS = ["chime", "canfar", "kko", "gbo", "hco", "local", "dev"]


# def set_site(count: int = 0):
#     """Set the SITE environment variable."""
#     logger.warn("The SITE environment variable must be set.")

#     # Select the site from a list of options.
#     for idx, site in enumerate(_SITE_OPTIONS):
#         print(f"{idx}: {site}")
#     site_idx = input("Select a Site (0-6): ")
#     try:
#         site = _SITE_OPTIONS[int(site_idx)]
#         logger.info(f"Setting SITE to {site} for this command.")
#         logger.warn(
#             f'[bold]Please run: "export SITE={site}" to avoid this message.[/bold]',
#             extra={"markup": True},
#         )
#         os.environ["SITE"] = site
#     except Exception as error:
#         count += 1
#         logger.warn(error)
#         if count == 2:
#             logger.error("Unable to set SITE.")
#             raise ValueError("Unable to set SITE.")
#         set_site(count)


# CONFIG = yaml.safe_load(
#     open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml"))
# )


# SITE = os.environ.get("SITE", None)

# if SITE is None:
#     try:
#         set_site()
#         SITE = os.environ.get("SITE", None)
#         if SITE is None:
#             logger.error("Site not set.")
#             raise ValueError("Site not set.")
#     except Exception as error:
#         logger.error(error)
#         raise error

# SERVER = CONFIG["server"][SITE]
# CERTFILE = CONFIG["vospace_certfile"][SITE]
# MOUNTS = CONFIG["root_mounts"]
