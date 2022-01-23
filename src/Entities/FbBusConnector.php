<?php declare(strict_types = 1);

/**
 * FbBusConnector.php
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
use IPub\DoctrineCrud\Mapping\Annotation as IPubDoctrine;

/**
 * @ORM\Entity
 */
class FbBusConnector extends DevicesModuleEntities\Connectors\Connector implements IFbBusConnector
{

	public const CONNECTOR_TYPE = 'fb-bus';

	/**
	 * @var int|null
	 * @IPubDoctrine\Crud(is="writable")
	 */
	protected ?int $address = null;

	/**
	 * @var string|null
	 * @IPubDoctrine\Crud(is="writable")
	 */
	protected ?string $serialInterface = null;

	/**
	 * @var int|null
	 * @IPubDoctrine\Crud(is="writable")
	 */
	protected ?int $baudRate = null;

	/**
	 * {@inheritDoc}
	 */
	public function getType(): string
	{
		return self::CONNECTOR_TYPE;
	}

	/**
	 * {@inheritDoc}
	 */
	public function getAddress(): ?int
	{
		return $this->getParam('address');
	}

	/**
	 * {@inheritDoc}
	 */
	public function setAddress(int $address): void
	{
		$this->setParam('address', $address);
	}

	/**
	 * {@inheritDoc}
	 */
	public function getSerialInterface(): ?string
	{
		return $this->getParam('serial_interface');
	}

	/**
	 * {@inheritDoc}
	 */
	public function setSerialInterface(string $serialInterface): void
	{
		$this->setParam('serial_interface', $serialInterface);
	}

	/**
	 * {@inheritDoc}
	 */
	public function getBaudRate(): ?int
	{
		return $this->getParam('baud_rate');
	}

	/**
	 * {@inheritDoc}
	 */
	public function setBaudRate(?int $baudRate): void
	{
		$this->setParam('baud_rate', $baudRate);
	}

	/**
	 * {@inheritDoc}
	 */
	public function toArray(): array
	{
		return array_merge(parent::toArray(), [
			'address'          => $this->getAddress(),
			'serial_interface' => $this->getSerialInterface(),
			'baud_rate'        => $this->getBaudRate(),
		]);
	}

	/**
	 * {@inheritDoc}
	 */
	public function getDiscriminatorName(): string
	{
		return self::CONNECTOR_TYPE;
	}

}
