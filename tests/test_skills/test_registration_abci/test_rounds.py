# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Test the rounds.py module of the skill."""

import json
from typing import Any, Dict, Optional, cast
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData as SynchronizedData,
)
from packages.valory.skills.registration_abci.payloads import RegistrationPayload
from packages.valory.skills.registration_abci.rounds import Event
from packages.valory.skills.registration_abci.rounds import Event as RegistrationEvent
from packages.valory.skills.registration_abci.rounds import (
    RegistrationRound,
    RegistrationStartupRound,
)

from tests.test_skills.test_abstract_round_abci.test_base_rounds import (
    BaseCollectDifferentUntilAllRoundTest,
    BaseCollectSameUntilThresholdRoundTest,
)


class TestRegistrationStartupRound(BaseCollectDifferentUntilAllRoundTest):
    """Test RegistrationStartupRound."""

    _synchronized_data_class = SynchronizedData
    _event_class = RegistrationEvent

    def test_run_fastforward(
        self,
    ) -> None:
        """Run test."""

        self.synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )

        test_round = RegistrationStartupRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        self._run_with_round(
            test_round,
            RegistrationEvent.FAST_FORWARD,
            1,
            initialisation=json.dumps({"key": "value"}),
        )

    def test_run_default(
        self,
    ) -> None:
        """Run test."""

        test_round = RegistrationStartupRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        self._run_with_round(test_round, RegistrationEvent.DONE, 1)

    def test_run_default_not_finished(
        self,
    ) -> None:
        """Run test."""

        test_round = RegistrationStartupRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        self._run_with_round(test_round)

    def _run_with_round(
        self,
        test_round: RegistrationStartupRound,
        expected_event: Optional[RegistrationEvent] = None,
        confirmations: Optional[int] = None,
        initialisation: Optional[str] = None,
    ) -> None:
        """Run with given round."""

        test_runner = self._test_round(
            test_round=test_round,
            round_payloads=[
                RegistrationPayload(sender=participant, initialisation=initialisation)
                for participant in self.participants
            ],
            synchronized_data_update_fn=lambda *x: SynchronizedData(
                AbciAppDB(
                    initial_data=dict(participants=[frozenset(test_round.collection)]),
                )
            ),
            synchronized_data_attr_checks=[
                lambda _synchronized_data: _synchronized_data.participants
            ],
            exit_event=expected_event,
        )

        next(test_runner)
        test_round = next(test_runner)
        if confirmations is not None:
            test_round.block_confirmations = confirmations
        prior_confirmations = test_round.block_confirmations

        next(test_runner)
        assert test_round.block_confirmations == prior_confirmations + 1
        next(test_runner)


class TestRegistrationRound(BaseCollectSameUntilThresholdRoundTest):
    """Test RegistrationRound."""

    _synchronized_data_class = SynchronizedData
    _event_class = RegistrationEvent

    def test_run_default(
        self,
    ) -> None:
        """Run test."""
        self.synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )
        test_round = RegistrationRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        round_payloads = {
            participant: RegistrationPayload(
                sender=participant,
                initialisation='{"dummy_key": "dummy_value"}',
            )
            for participant in self.participants
        }

        self._run_with_round(
            test_round=test_round,
            expected_event=RegistrationEvent.DONE,
            confirmations=10,
            most_voted_payload='{"dummy_key": "dummy_value"}',
            round_payloads=round_payloads,
        )

        assert self.synchronized_data.db._data[0]["dummy_key"] == ["dummy_value"]

    def test_run_default_not_finished(
        self,
    ) -> None:
        """Run test."""
        self.synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )
        test_round = RegistrationRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        self._run_with_round(test_round, finished=False)

    def _run_with_round(
        self,
        test_round: RegistrationRound,
        round_payloads: Optional[Dict[str, RegistrationPayload]] = None,
        most_voted_payload: Optional[Any] = None,
        expected_event: Optional[RegistrationEvent] = None,
        confirmations: Optional[int] = None,
        finished: bool = True,
    ) -> None:
        """Run with given round."""

        round_payloads = round_payloads or {
            p: RegistrationPayload(sender=p) for p in self.participants
        }

        test_runner = self._test_round(
            test_round=test_round,
            round_payloads=round_payloads,
            synchronized_data_update_fn=(
                lambda *x: SynchronizedData(
                    AbciAppDB(
                        initial_data=dict(participants=[self.participants]),
                    )
                )
            ),
            synchronized_data_attr_checks=[
                lambda _synchronized_data: _synchronized_data.participants
            ],
            most_voted_payload=most_voted_payload,
            exit_event=expected_event,
        )

        next(test_runner)
        test_round = next(test_runner)
        if confirmations is not None:
            test_round.block_confirmations = confirmations
        prior_confirmations = test_round.block_confirmations

        next(test_runner)
        assert test_round.block_confirmations == prior_confirmations + 1
        if finished:
            next(test_runner)

    def test_no_majority(self) -> None:
        """Test the NO_MAJORITY event."""
        test_round = RegistrationRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        with mock.patch.object(test_round, "is_majority_possible", return_value=False):
            result = test_round.end_block()
            assert result is not None
            _, event = result
            assert event == Event.NO_MAJORITY
