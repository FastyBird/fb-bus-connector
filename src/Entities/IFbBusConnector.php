<?php declare(strict_types = 1);

/**
 * IFbBusConnector.php
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
use FastyBird\FbBusConnector\Types;

/**
 * FastyBird BUS connector entity interface
 *
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Entities
 *
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 */
interface IFbBusConnector extends DevicesModuleEntities\Connectors\IConnector
{

	/**
	 * @return int
	 */
	public function getAddress(): int;

	/**
	 * @return string
	 */
	public function getInterface(): string;

	/**
	 * @return int
	 */
	public function getBaudRate(): int;

	/**
	 * @return Types\ProtocolVersionType
	 */
	public function getProtocol(): Types\ProtocolVersionType;

}
