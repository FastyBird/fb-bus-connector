<?php declare(strict_types = 1);

/**
 * FbBusDeviceHydrator.php
 *
 * @license        More in LICENSE.md
 * @copyright      https://www.fastybird.com
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Hydrators
 * @since          0.1.0
 *
 * @date           22.01.22
 */

namespace FastyBird\FbBusConnector\Hydrators;

use FastyBird\DevicesModule\Hydrators as DevicesModuleHydrators;
use FastyBird\FbBusConnector\Entities;

/**
 * FastyBird BUS device entity hydrator
 *
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Hydrators
 *
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 *
 * @phpstan-extends DevicesModuleHydrators\Devices\DeviceHydrator<Entities\IFbBusDevice>
 */
final class FbBusDeviceHydrator extends DevicesModuleHydrators\Devices\DeviceHydrator
{

	/**
	 * {@inheritDoc}
	 */
	public function getEntityName(): string
	{
		return Entities\FbBusDevice::class;
	}

}
