import os
import shutil
from zentral.utils.osx_package import EnrollmentPackageBuilder
from zentral.utils.filebeat_releases import Releases as FilebeatReleases
from zentral.contrib.filebeat.scepclient_releases import Releases as ScepClientReleases

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ZentralFilebeatPkgBuilder(EnrollmentPackageBuilder):
    name = "Zentral Filebeat"
    package_name = "zentral_filebeat.pkg"
    base_package_identifier = "io.zentral.filebeat"
    build_tmpl_dir = os.path.join(BASE_DIR, "build.tmpl")
    standalone = True

    def __init__(self, enrollment, version=None):
        super().__init__(enrollment, version,
                         release=enrollment.filebeat_release)

    def extra_build_steps(self):
        # filebeat binary
        release = self.build_kwargs["release"]
        if release:
            r = FilebeatReleases()
            local_path = r.get_requested_package(self.build_kwargs["release"])
            filebeat_path = self.get_root_path("usr/local/zentral/bin/filebeat")
            filebeat_dir = os.path.dirname(filebeat_path)
            if not os.path.exists(filebeat_dir):
                os.makedirs(filebeat_dir)
            shutil.copy(local_path, filebeat_path)

        # scepclient binary
        local_path = ScepClientReleases("darwin").get_a_version()
        if local_path:
            scepclient_path = self.get_root_path("usr/local/zentral/bin/scepclient")
            scepclient_dir = os.path.dirname(scepclient_path)
            if not os.path.exists(scepclient_dir):
                os.makedirs(scepclient_dir)
            shutil.copy(local_path, scepclient_path)

        # postinstall
        postinstall_script = self.get_build_path("scripts", "postinstall")
        self.replace_in_file(postinstall_script,
                             (("%ENROLLMENT_SECRET%", self.build_kwargs["enrollment_secret_secret"]),
                              ("%TLS_HOSTNAME%", self.get_tls_hostname()),
                              ("%TLS_SERVER_CERTS%", self.include_tls_server_certs() or "")))
