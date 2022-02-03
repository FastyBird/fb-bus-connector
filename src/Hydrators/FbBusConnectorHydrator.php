<?php declare(strict_types = 1);

/**
 * FbBusConnectorHydrator.php
 *
 * @license        More in LICENSE.md
 * @copyright      https://www.fastybird.com
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Hydrators
 * @since          0.4.0
 *
 * @date           23.01.22
 */

namespace FastyBird\FbBusConnector\Hydrators;

use FastyBird\DevicesModule\Hydrators as DevicesModuleHydrators;
use FastyBird\FbBusConnector\Entities;
use FastyBird\FbBusConnector\Types;
use FastyBird\JsonApi\Exceptions as JsonApiExceptions;
use Fig\Http\Message\StatusCodeInterface;
use IPub\JsonAPIDocument;

/**
 * FastyBird BUS Connector entity hydrator
 *
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Hydrators
 *
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 *
 * @phpstan-extends DevicesModuleHydrators\Connectors\ConnectorHydrator<Entities\IFbBusConnector>
 */
final class FbBusConnectorHydrator extends DevicesModuleHydrators\Connectors\ConnectorHydrator
{

	/** @var string[] */
	protected array $attributes = [
		0 => 'name',
		1 => 'enabled',
		2 => 'address',
		3 => 'interface',
		4 => 'protocol',

		'baud_rate' => 'baudRate',
	];

	/**
	 * {@inheritDoc}
	 */
	public function getEntityName(): string
	{
		return Entities\FbBusConnector::class;
	}

	/**
	 * @param JsonAPIDocument\Objects\IStandardObject $attributes
	 *
	 * @return int|null
	 */
	protected function hydrateAddressAttribute(JsonAPIDocument\Objects\IStandardObject $attributes): ?int
	{
		if (
			!is_scalar($attributes->get('address'))
			|| (string) $attributes->get('address') === ''
		) {
			return null;
		}

		return (int) $attributes->get('address');
	}

	/**
	 * @param JsonAPIDocument\Objects\IStandardObject $attributes
	 *
	 * @return string|null
	 */
	protected function hydrateInterfaceAttribute(JsonAPIDocument\Objects\IStandardObject $attributes): ?string
	{
		if (
			!is_scalar($attributes->get('interface'))
			|| (string) $attributes->get('interface') === ''
		) {
			return null;
		}

		return (string) $attributes->get('interface');
	}

	/**
	 * @param JsonAPIDocument\Objects\IStandardObject $attributes
	 *
	 * @return int|null
	 */
	protected function hydrateBaudRateAttribute(JsonAPIDocument\Objects\IStandardObject $attributes): ?int
	{
		if (
			!is_scalar($attributes->get('baud_rate'))
			|| (string) $attributes->get('baud_rate') === ''
		) {
			return null;
		}

		return (int) $attributes->get('baud_rate');
	}

	/**
	 * @param JsonAPIDocument\Objects\IStandardObject $attributes
	 *
	 * @return Types\ProtocolVersionType|null
	 */
	protected function hydrateProtocolAttribute(JsonAPIDocument\Objects\IStandardObject $attributes): ?Types\ProtocolVersionType
	{
		if (
			!is_scalar($attributes->get('protocol'))
			|| (string) $attributes->get('protocol') === ''
		) {
			return null;
		}

		if (!Types\ProtocolVersionType::isValidValue((int) $attributes->get('protocol'))) {
			throw new JsonApiExceptions\JsonApiErrorException(
				StatusCodeInterface::STATUS_UNPROCESSABLE_ENTITY,
				$this->translator->translate('//fb-bus-connector.base.messages.invalidAttribute.heading'),
				$this->translator->translate('//fb-bus-connector.base.messages.invalidAttribute.message'),
				[
					'pointer' => 'data/protocol',
				]
			);
		}

		return Types\ProtocolVersionType::get((int) $attributes->get('protocol'));
	}

}
