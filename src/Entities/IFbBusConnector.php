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

/**
 * FastyBird BUS connector entity interface
 *
 * @package        FastyBird:v!
 * @subpackage     Entities
 *
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 */
interface IFbBusConnector extends IConnector
{

	/**
	 * @return int|null
	 */
	public function getAddress(): ?int;

	/**
	 * @param int $address
	 *
	 * @return void
	 */
	public function setAddress(int $address): void;

	/**
	 * @return string|null
	 */
	public function getSerialInterface(): ?string;

	/**
	 * @param string $serialInterface
	 *
	 * @return void
	 */
	public function setSerialInterface(string $serialInterface): void;

	/**
	 * @return int|null
	 */
	public function getBaudRate(): ?int;

	/**
	 * @param int|null $baudRate
	 *
	 * @return void
	 */
	public function setBaudRate(?int $baudRate): void;

}
