
#!/usr/bin/env sh

cp ../configure_agents/keys/ethereum_private_key_1.txt ethereum_private_key.txt
aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.source_id binance
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants 6
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.keeper_timeout_seconds 5
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://node1:26657
aea config set vendor.fetchai.connections.ledger.config.ledger_apis.ethereum.address http://hardhat:8545
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.convert_id USDT
aea build
