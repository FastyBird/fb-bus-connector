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

		'serial_interface' => 'serialInterface',
		'baud_rate'        => 'baudRate',
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
	protected function hydrateSerialInterfaceAttribute(JsonAPIDocument\Objects\IStandardObject $attributes): ?string
	{
		if (
			!is_scalar($attributes->get('serial_interface'))
			|| (string) $attributes->get('serial_interface') === ''
		) {
			return null;
		}

		return (string) $attributes->get('serial_interface');
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

}
