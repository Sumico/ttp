Group Attributes
================

Each group tag (<g>, <group>)can have a number of attributes, they used during module execution to provide desired outcome. Attributes can be mandatory or optional. Each attribute is a string that canbe formatted in certain way and can contain additional data.

**Specification**

.. list-table::
   :widths: 10 20 20 50
   :header-rows: 1
   :align: left

   * - Attribute Name
     - Example
	 - Mandatory/
	   Optional
     - Description
   * - **name**  
     - name="interfaces.vlans"
	 - **Mandatory**
     - Uniquely identifies group within template and specifies results path location
   * - **input** 
     - input="./Data/DC1/"
	 - Optional
     - Used to provide the name of input tag which will beparsed bygiven group, 
	   alternatively can contain OS path string to files location that needs to be parsed by this group
