<?php declare(strict_types = 1);

/**
 * FbBusDevice.php
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

use Doctrine\ORM\Mapping as ORM;
use FastyBird\DevicesModule\Entities as DevicesModuleEntities;

/**
 * @ORM\Entity
 */
class FbBusDevice extends DevicesModuleEntities\Devices\Device implements IFbBusDevice
{

	public const DEVICE_TYPE = 'fb-bus';

	/**
	 * {@inheritDoc}
	 */
	public function getType(): string
	{
		return self::DEVICE_TYPE;
	}

	/**
	 * {@inheritDoc}
	 */
	public function getDiscriminatorName(): string
	{
		return self::DEVICE_TYPE;
	}

}
