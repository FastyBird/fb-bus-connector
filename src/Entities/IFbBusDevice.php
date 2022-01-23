<?php declare(strict_types = 1);

/**
 * IFbBusDevice.php
 *
 * @license        More in LICENSE.md
 * @copyright      https://www.fastybird.com
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Entities
 * @since          0.4.0
 *
 * @date           23.01.22
 */

namespace FastyBird\FbBusConnector\Entities;

use FastyBird\DevicesModule\Entities as DevicesModuleEntities;

/**
 * FastyBird BUS device entity interface
 *
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Entities
 *
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 */
interface IFbBusDevice extends DevicesModuleEntities\Devices\IDevice
{

}
