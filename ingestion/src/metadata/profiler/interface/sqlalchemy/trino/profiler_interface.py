#  Copyright 2021 Collate
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
Interfaces with database for all database engine
supporting sqlalchemy abstraction layer
"""

from typing import List

from sqlalchemy import func
from sqlalchemy.exc import ProgrammingError

from metadata.profiler.interface.sqlalchemy.profiler_interface import (
    SQAProfilerInterface,
    handle_query_exception,
)
from metadata.profiler.metrics.registry import Metrics
from metadata.profiler.orm.registry import FLOAT_SET
from metadata.profiler.processor.runner import QueryRunner
from metadata.utils.logger import profiler_interface_registry_logger

logger = profiler_interface_registry_logger()


class TrinoProfilerInterface(SQAProfilerInterface):
    """
    Interface to interact with registry supporting
    sqlalchemy.
    """

    def _compute_window_metrics(
        self,
        metrics: List[Metrics],
        runner: QueryRunner,
        *args,
        **kwargs,
    ):
        """Given a list of metrics, compute the given results
        and returns the values

        Args:
            column: the column to compute the metrics against
            metrics: list of metrics to compute
        Returns:
            dictionnary of results
        """
        session = kwargs.get("session")
        column = kwargs.get("column")

        if not metrics:
            return None
        try:
            runner_kwargs = {}
            if column.type in FLOAT_SET:
                runner_kwargs = {
                    "query_filter_": {"filters": [(func.is_nan(column), "eq", False)]}
                }
            row = runner.select_first_from_sample(
                *[metric(column).fn() for metric in metrics], **runner_kwargs
            )
        except ProgrammingError as err:
            logger.info(
                f"Skipping window metrics for {runner.table.__tablename__}.{column.name} due to {err}"
            )
            return None

        except Exception as exc:
            msg = f"Error trying to compute profile for {runner.table.__tablename__}.{column.name}: {exc}"
            handle_query_exception(msg, exc, session)
        if row:
            return dict(row)
        return None
