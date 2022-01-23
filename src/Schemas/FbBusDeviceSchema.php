<?php declare(strict_types = 1);

/**
 * FbBusDeviceSchema.php
 *
 * @license        More in LICENSE.md
 * @copyright      https://www.fastybird.com
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Schemas
 * @since          0.4.0
 *
 * @date           23.01.22
 */

namespace FastyBird\FbBusConnector\Schemas;

use FastyBird\DevicesModule\Schemas as DevicesModuleSchemas;
use FastyBird\FbBusConnector\Entities;

/**
 * FastyBird BUS connector entity schema
 *
 * @package         FastyBird:FbBusConnector!
 * @subpackage      Schemas
 *
 * @author          Adam Kadlec <adam.kadlec@fastybird.com>
 *
 * @phpstan-extends DevicesModuleSchemas\Devices\DeviceSchema<Entities\IFbBusDevice>
 */
final class FbBusDeviceSchema extends DevicesModuleSchemas\Devices\DeviceSchema
{

	/**
	 * Define entity schema type string
	 */
	public const SCHEMA_TYPE = 'devices-module/device-fb-bus';

	/**
	 * {@inheritDoc}
	 */
	public function getEntityClass(): string
	{
		return Entities\FbBusDevice::class;
	}

	/**
	 * @return string
	 */
	public function getType(): string
	{
		return self::SCHEMA_TYPE;
	}

}
