# webapp/services/layers/repository_service.py

import logging

from .repository_client import RepositoryClient
from .repository_interpreter import RepositoryInterpreter

logger = logging.getLogger(__name__)

class RepositoryService:

    @staticmethod
    def analyse(group_id, artifact_id, version):
        logger.info("[RepositoryService] Analysing %s:%s:%s", group_id, artifact_id, version)

        metadata = RepositoryClient.load_index(group_id, artifact_id)
        result = RepositoryInterpreter.interpret(metadata, version)

        logger.info("[RepositoryService] Result=%s",result["status"])
        return result